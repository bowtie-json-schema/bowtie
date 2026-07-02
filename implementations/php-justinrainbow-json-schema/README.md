# Justinrainbow/json-schema implementation
This folder contains the test harness for the justinrainbow/json-schema implementation.

# Easy to use commands
You can check composer scripts for easy to use commands.

Al commands assume you have a local container which can be made available using
```bash
composer build-container
```

You can run test using the following command:
```bash
composer run-suite-draft3
composer run-suite-draft4
composer run-suite-draft6
composer run-suite-draft7
composer run-suite-draft2019-09

# Or if you want a report
composer run-suite-draft3 | bowtie summary --format markdown > draft3-report.md
composer run-suite-draft4 | bowtie summary --format markdown > draft4-report.md
composer run-suite-draft6 | bowtie summary --format markdown > draft6-report.md
composer run-suite-draft7 | bowtie summary --format markdown > draft7-report.md
composer run-suite-draft2019-09 | bowtie summary --format markdown > draft2019-09-report.md

# Or if you want a summary of failures
composer run-suite-draft3 | bowtie summary --format markdown --show failures > draft3-failures.md
composer run-suite-draft4 | bowtie summary --format markdown --show failures > draft4-failures.md
composer run-suite-draft6 | bowtie summary --format markdown --show failures > draft6-failures.md
composer run-suite-draft7 | bowtie summary --format markdown --show failures > draft7-failures.md
composer run-suite-draft2019-09 | bowtie summary --format markdown --show failures > draft201909-failures.md
```
