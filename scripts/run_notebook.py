"""Execute notebook cells headlessly; preserve golden files unless explicitly refreshed."""


def main():
    import json
    import os
    import sys
    from pathlib import Path

    PROJECT = Path(__file__).resolve().parents[1]
    ROOT = PROJECT
    os.environ["HF_HOME"] = str(ROOT / ".cache/huggingface")
    os.environ["MPLCONFIGDIR"] = str(ROOT / ".cache/mpl")
    os.environ["MPLBACKEND"] = "Agg"
    os.environ["OMP_NUM_THREADS"] = "2"
    os.environ["DISABLE_SAFETENSORS_CONVERSION"] = "1"
    os.chdir(PROJECT)
    import matplotlib.pyplot as plt
    import torch

    torch.set_num_threads(2)
    nb = json.loads((PROJECT / "tracks/vision/notebook.ipynb").read_text())
    ns = {}
    fig_no = 0

    def show():
        nonlocal fig_no
        fig_no += 1
        plt.savefig(PROJECT / f"evidence/notebook-figure-{fig_no}.png", dpi=130, bbox_inches="tight")
        plt.close("all")

    plt.show = show
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code" or i == 2:
            continue
        source = "".join(c["source"])
        source = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("%"))
        print(f"RUNNING ORIGINAL NOTEBOOK CELL {i}", flush=True)
        exec(compile(source, f"notebook-cell-{i}", "exec"), ns)
        if i == 12 and (
            not (PROJECT / "tests/fixtures/golden.json").exists() or "--refresh-golden" in sys.argv
        ):
            dest = PROJECT / "tests/fixtures"
            dest.mkdir(parents=True, exist_ok=True)
            cases = []
            for idx in [0, 43, 50, 86, 100]:
                filename = f"leaf-{idx}.png"
                ns["test_ds"][idx]["image"].convert("RGB").save(dest / filename)
                cases.append(
                    {
                        "index": idx,
                        "file": filename,
                        "true_label": ns["label_names"][ns["labels"][idx]],
                        "scores": ns["all_probs"][idx].tolist(),
                    }
                )
            (dest / "golden.json").write_text(
                json.dumps(
                    {
                        "source": "Original notebook cell 12, before service refactoring",
                        "model_revision": ns["model_revision"],
                        "dataset_revision": ns["data_revision"],
                        "cases": cases,
                    },
                    indent=2,
                )
            )
    print("ORIGINAL NOTEBOOK COMPLETE", flush=True)


if __name__ == "__main__":
    main()
