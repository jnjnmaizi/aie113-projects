# Project guide: from a notebook to a real AI service

**SDA-AIE-113 · Software Engineering Practices for AI Systems · SDAIA Academy**
[النسخة العربية](GUIDE.ar.md)

This guide is for every trainee, including those who have never written a line of Python or
seen a machine-learning model. You will not write code by hand. Your AI coding agent writes the
code. **Your job is to decide, to check, and to understand.** If your group can explain what was
built at each stage, why, and how you checked it, you get full marks.

Each stage below has the same parts:

- **The idea**: what this stage is about, in plain words.
- **Ask your agent**: things to say to your agent. Use your own words; these are examples.
- **See it yourself**: how to look at what the agent built, so you are never in the dark.
- **Done when**: how you know the stage is finished.
- **For your journal**: what to write down.

---

## Before you start: how to work with an agent and still understand everything

### The loop for every stage

1. **Understand.** Ask the agent to explain the stage's idea using *your* project, before it
   changes anything.
2. **Plan.** Ask for a short plan: which files it will create or change, and why. Agree on it.
3. **Build in small steps.** One step at a time. Never accept a huge change you cannot follow.
4. **See it.** Run it, open it, try it, break it on purpose. The "See it yourself" lists help.
5. **Record.** Write the journal entry while it is fresh.

### Questions that always work

- "Explain what you just did in plain words, as if I have never programmed."
- "Show me the folder tree and explain each folder in one line."
- "Which file would change if we wanted to …?"
- "What could go wrong here, and how would we notice?"
- "Show me the changes since the last commit and explain them line by line."
- "Run it and show me the output. What should I expect to see?"
- "Is there a simpler way? What are we giving up?"

### Warning signs

Stop and ask when the agent changes many files at once, deletes or weakens a test to make
something pass, puts a password or key in a file, says something works without showing it, or
uses a word you do not understand. You are in charge.

### Groups and roles

Groups can be any size. **At least one member needs an AI coding agent backed by a frontier
model** (for example Claude Code, GitHub Copilot in agent mode, Cursor, Codex or Gemini CLI).
The rest is up to you. A good split, rotated at every stage:

- **Driver**: talks to the agent.
- **Checker**: runs things and compares the result with what was promised.
- **Scribe**: writes the journal.
- **Explainer**: at the end of the stage, explains it to the others in two minutes. If they
  cannot, the stage is not finished.

---

## Stage 0: Pick a track and meet your model

### The idea
Every project starts from a real notebook, the kind a data scientist hands over: it works on
their laptop, it is one long file, and nobody else can run it in production. Choose one track:

| Track | What the model does | Explanation it gives |
|---|---|---|
| [Vision](tracks/vision/) | Spots disease on bean leaves in real field photos, with a published model | Which part of the leaf the model looked at |

### Ask your agent
- "Read `tracks/<track>/README.md` and the notebook. Explain the model to me in five sentences:
  what goes in, what comes out, how it learned, how good it is, and where it fails."
- "What is the baseline in this notebook, and why does it matter?"

### See it yourself
Open the notebook in Colab (link at the top of the notebook) and run every cell. Find the cell
that loads the data, the one that trains or loads the model, the evaluation numbers, and the
explanation.

### Done when
Every member can say in one minute what the model does and what "good" means for it.

### For your journal
The track, why you chose it, the model in your own words, and its key number.

---

## Stage 1: Reorganise the notebook (clean architecture)

### The idea
A notebook mixes everything: loading data, business rules, the model, file paths, printing. In
a service, each of those has its own place, so you can change one without breaking the others.

The clean-architecture picture from Module 1:

- **Domain** (the centre): the words and rules of your problem, with no tools mixed in. For
  example "a transaction", "a forecast", "a leaf diagnosis", "block above this score".
- **Service** (use cases): the steps of one job, such as "score this transaction".
- **Adapters** (the edge): the tools. The model library, the data source, files, the web.
- **Entry points**: how the outside world starts a job: a command, a web endpoint.
- **Configuration** in one place, never scattered as constants.

The golden rule: inner parts never depend on outer parts. If you swap the model or the data
source, only an adapter changes.

**Other architectures are welcome.** Hexagonal ("ports and adapters"), a simple pipeline of
modules, or another style your agent proposes are all fine, as long as your group can explain
where each part lives and why.

**Keep the notebook's answers.** Before the agent moves any code, save the notebook's outputs
for a few inputs. After the reorganisation, the new code must give the same answers. That is
your proof nothing broke (we called this a "golden" check in Module 1).

### Track hints
- **Stocks:** the price source (Yahoo Finance today, maybe a paid provider tomorrow) is an
  adapter behind a small interface. Feature building must use only the past.
- **Fraud:** the explanation ("top reasons") is part of the service's job, not an afterthought.
  The alert threshold is a business rule, so it belongs in the domain or in configuration.
- **Vision:** image preparation (resize, colours) must be exactly the same in every place that
  uses the model. The model download belongs in an adapter.

### Ask your agent
- "Propose a structure for this project. Show me the folder tree, and for each folder say in
  one line what lives there and what it may not import."
- "Before moving any code, save the notebook's outputs for 5 example inputs so we can check
  that the new code gives the same answers."
- "Which file would change if we replaced the model? If we replaced the data source?"

### See it yourself
Read the folder tree. Ask the agent to draw the import directions as a list of arrows. Run the
golden check and see the answers match. Open one domain file and check it imports no model or
web library.

### Done when
The project runs from the new structure (no notebook needed), gives the notebook's answers,
and every member can point to where the data, the rules, the model and the configuration live.

### For your journal
The folder tree with one line per folder, the golden check result, and one sentence on why
you chose this architecture.

---

## Stage 2: Put an API in front of it (FastAPI)

### The idea
An API is a door with clear rules: what you must send, what you get back, and what happens when
you send something wrong. Other systems (an app, a website, a bank's core system) use your
model only through this door.

- **The contract**: the exact shape of a request and a response. FastAPI checks every request
  against it (with a library called pydantic) and rejects bad ones with a clear message.
- **Errors**: one predictable error shape, and never private data or internal details in it.
- **Health and readiness**: one address answers "is the process alive?", another "is the model
  loaded and ready?".
- **Load the model once**, when the service starts, not on every request.
- **Version the API** (for example `/v1/...`) so you can improve it later without breaking users.
- FastAPI builds an interactive documentation page at `/docs` from your contract for free.

### Track hints
- **Stocks:** send a ticker; get the forecast for the next trading day, the naive baseline next
  to it, the date of the latest price used, and a "not investment advice" note. Unknown
  tickers get a clear rejection.
- **Fraud:** send one transaction; get a fraud probability, a decision (allow, review, block)
  and the top reasons.
- **Vision:** upload a photo; get the predicted condition, a confidence, and "not sure" when the
  confidence is low. Reject files that are not images or are too large.

### Ask your agent
- "Design the request and response for our endpoint. Show them as examples before writing code."
- "What happens if someone sends a wrong or missing field? Show me the error they get."
- "Explain the difference between our health and readiness endpoints."

### See it yourself
Start the service and open `http://localhost:8000/docs`. Try a good request, then break it:
a missing field, a wrong type, a silly value. Read every response. Check that the error never
echoes private data.

### Done when
The documentation page works, good requests get sensible answers with explanations, and bad
requests get clear, safe errors.

### For your journal
One good request and its response, one bad request and its error, and what the readiness
check looks at.

---

## Stage 3: Put it in a container (Docker)

### The idea
"It works on my laptop" is not good enough. A container packs your service with everything it
needs (the operating system's libraries, Python, the libraries, the model) so it runs the same
way everywhere.

- **Image** = the packed recipe result. **Container** = a running copy of an image.
- **Lock the dependencies**: write down the exact version of every library, so every build
  installs the same thing.
- **Small and safe**: start from a slim base image, use a multi-stage build (build tools stay
  behind), run as a normal user (not root), and never copy secrets into the image.
- **Health check**: the container reports whether it is ready, using your readiness endpoint.
- **Docker Compose** starts your service (and anything it needs) with one command.
- **The model**: inside the image (simple, all-or-nothing updates) or downloaded at start
  (smaller image, but start-up depends on the download). Choose and explain.

### Track hints
- **Vision:** the model is large and PyTorch is very large. Ask about a smaller runtime (such as
  ONNX Runtime) and compare image sizes.
- **Stocks:** the service needs internet access to fetch prices. Decide what happens when the
  price source is down (a clear error? the last saved prices with their date?).
- **Fraud:** the model is small; focus on making the image slim and non-root.

### Ask your agent
- "Write a Dockerfile and explain every line. Why this base image? What does each stage keep?"
- "How big is the image, and what makes up most of it? How could we make it smaller?"
- "Show me that the container does not run as root and contains no secrets."

### See it yourself
Build the image and note its size and build time. Run it and call `/docs` through the
container. Check the health status. Change one line of code, rebuild, and see how much faster
the second build is.

### Done when
One command starts the service in a container, it reports healthy, and your group can explain
what is inside the image and why.

### For your journal
Image size, build time, rebuild time, the user the container runs as, and where the model lives.

---

## Stage 4: Test it (and know what you are testing)

### The idea
Tests are small automatic checks that tell you, in seconds, whether something broke. An AI
system needs two kinds: tests that catch **broken code**, and tests that catch **a model that
no longer behaves as promised** (it can be wrong while everything "runs fine").

Think of it as a pyramid: many small fast tests at the bottom, fewer slower ones at the top.

| Level | What it checks | Examples of ideas |
|---|---|---|
| **Unit** | One small piece of logic, alone, in milliseconds | A business rule (score above the threshold → "block"); feature building gives the right numbers for a known input |
| **Integration** | The API from the outside, like a real client | A good request gets the promised shape; every kind of bad request is rejected; errors leak nothing |
| **Model behaviour** | How the real model behaves | Invariance (changing something irrelevant must not change the answer); direction (changing something meaningful must move the answer the right way); a minimum quality on reference data; comparison with the baseline |
| **Golden / regression** | The same inputs still give the same answers | The answers you saved from the notebook in Stage 1 |
| **Data checks** | The input data is what you expect | Columns present, values in sensible ranges, no future data mixed in |
| **Smoke test** | The container really starts and answers | Start it, call readiness and one request |

Good habits: use a **fake model** for fast tests (a stand-in that returns a known score), keep
the real model for the behaviour tests, make tests repeatable (same answer every run), and
**never delete or weaken a test to make it pass**: find the cause.

### Track test ideas
- **Stocks:** features use only past prices (the forecast for a day must not change if you
  delete all later days); the model is compared with the naive baseline on recent data and the
  result is reported honestly; missing days and market holidays do not crash it; an unknown
  ticker is rejected; the forecast is a positive number in a sensible range.
- **Fraud:** the reasons always name real inputs; making a flagged transaction's top reason
  "typical" lowers its score; the decision matches the threshold; the share of frauds caught on
  reference data stays above an agreed level; an empty or impossible transaction is rejected;
  no reason ever exposes private data.
- **Vision:** image preparation matches what the model expects (size, colour order); the same
  photo always gives the same answer; a slightly brighter or slightly rotated photo keeps its
  label; accuracy on a small set of reference photos stays above an agreed level; non-images and
  huge files are rejected; low confidence gives "not sure".

### Ask your agent
- "List the tests you plan to write, grouped by level, each in one plain sentence, before you
  write them."
- "Which of these tests would catch a model that silently got worse?"
- "Break something on purpose and show me which test catches it."
- "Run all tests and explain the result. Which parts of the code are not tested?"

### See it yourself
Run the tests and read the summary. Break one thing on purpose (a rule, a feature) and watch a
test fail, then undo it. Ask for the coverage report and the one untested part that worries
you most.

### Done when
Fast tests run in seconds, behaviour tests check the real model, and your group can say what
each test protects.

### For your journal
Your test list in plain words, the deliberate break and which test caught it, and the test run
time.

---

## Stage 5: Automate it (GitHub Actions)

### The idea
A pipeline is an automatic checklist that runs on every change you push to GitHub. People
forget steps; the pipeline never does. Typical jobs, in order:

1. **Lint**: style and simple mistakes.
2. **Test**: the fast tests (the slow ones can run nightly).
3. **Build** the image and run the **smoke test** against it.
4. **Publish** the image to a registry (for example GitHub's own), only from the main branch.

Then **protect the main branch**: changes arrive through pull requests, and a pull request can
only be merged when the checks are green. Give the pipeline the fewest permissions it needs, and
never write a secret in a workflow file.

### Ask your agent
- "Write a GitHub Actions workflow with lint, test, image build, smoke test and publish. Explain
  each job and when it runs."
- "Which permissions does each job have, and why?"
- "Help me switch on branch protection for main. What do I click in GitHub?"

### See it yourself
Open the Actions tab and watch a run. Click into a job and read its log. Then open a pull
request with a deliberate mistake (a failing test, for example) and see the merge button blocked.
Fix it properly and merge.

### Done when
Every push runs the pipeline, a broken change cannot reach main, and the image is published.

### For your journal
A screenshot of a blocked pull request, the job durations, and the image's address.

---

## Stage 6: Handle secrets the modern way

### The idea
A secret is anything that grants access: API keys, tokens, passwords, private keys. The rules
that never bend: **a secret is never in git, never in an image, never in a log.** Deleting a
leaked secret later is not enough, because copies remain: **rotate it first** (revoke and
replace), then clean up, then prevent it happening again.

Environment variables and a git-ignored `.env` file are the minimum. Modern practice goes
further, at each place a secret lives:

- **On a developer laptop**
  - **SOPS + age**: keep secrets *encrypted inside the repository*. age is a small, modern
    encryption tool: each member has a key pair, and the public keys are listed in the repo.
    SOPS encrypts only the values in a config file, so the file stays readable and reviewable
    while the secrets are not. Only people (and pipelines) holding a matching private key can
    decrypt. Private keys are never committed.
  - **A secrets manager's command-line tool** (for example 1Password CLI, Doppler or Infisical)
    that injects secrets into the program when it runs, so they never sit in a file at all.
- **In the pipeline**
  - **GitHub Actions secrets and environments**: encrypted, masked in logs, and an environment
    can require a person's approval before a deployment job may use them.
  - **OIDC federation** instead of stored cloud keys: GitHub proves to the cloud who the
    workflow is, and the cloud hands out a short-lived credential. Nothing long-lived is stored.
  - The built-in `GITHUB_TOKEN` with the fewest permissions possible.
- **When the service runs**
  - A **secret store** (AWS Secrets Manager, Google Secret Manager, Azure Key Vault, HashiCorp
    Vault) or the platform's secrets (Docker or Kubernetes secrets, mounted as files), read at
    start-up.
  - **Typed settings** that mark secret values so they are never printed, and **log masking**
    as a safety net.
- **Always**
  - **Secret scanning**: a scanner such as gitleaks before each commit and in the pipeline,
    plus GitHub's push protection, which blocks a push that contains a known key format.
  - **Short-lived and least-privilege**: a key that expires soon and can do little is a small
    loss if it leaks.
  - A short **incident plan**: who rotates what, in which order.

### Track hints
Your track may not need a real secret, so create a realistic one to practise with:
- **Stocks:** an API key for a paid market-data provider (the natural next step after Yahoo).
- **Fraud:** a token for an alerting webhook that notifies the fraud team.
- **Vision:** a Hugging Face access token for downloading a private model.

### Ask your agent
- "Set up SOPS with age for our project. Explain who holds which key, what is committed and what
  is not."
- "Show me that the committed secrets file is unreadable, and that the service still gets the
  value when it runs."
- "How would our pipeline get the secret? How would a production server get it?"
- "Add secret scanning before commit and in the pipeline. Then show me it catching a fake key."
- "Write our incident plan if this key leaked today."

### See it yourself
Open the encrypted file in GitHub and see that the values are unreadable. Try committing a fake
key and watch the scanner stop you. Check the service's logs: the secret must never appear.

### Done when
No secret exists in plain text in the repository, image or logs; the service and pipeline still
get what they need; and your group can explain the path a secret takes from creation to use.

### For your journal
The path of your secret (who creates it, where it is stored, how each place gets it), the
scanner catching a fake key, and your incident plan in five lines.

---

## Extension (optional): a front end with Vite and React

### The idea
A small web page that talks to your API: a form for the transaction, a box for the ticker, or a
photo upload, showing the answer and its explanation. Vite is a fast tool for building such
pages; React is a popular way to write them.

- The page calls your API; the browser must be allowed to call it (ask about CORS).
- **No secrets in front-end code**: anything in the page is visible to every visitor.
- The API address is configuration, not hard-coded.
- The built page can be served by a small web-server container next to your API, started
  together with Docker Compose.

This is an extra. It does not change your marks.

---

## Your journal and your marks

Keep `JOURNAL.md` in your repository (start from [the template](JOURNAL.md)). One entry per
stage. Your agent can draft it; your group must check and edit it.

**Marking: understanding is full marks.** Code quality, speed and the front end are not graded.
You show your understanding through:

1. **Your repository**: the project at each stage, built with your agent.
2. **Your journal**: one entry per stage.
3. **A short walkthrough** with your instructor: any member may be asked to explain any stage:
   what it is, why it matters, what you built, and how you checked it.

Asking for help, asking your agent "why?" a hundred times, and getting stuck are all part of the
work. Hiding a problem is the only real mistake.
