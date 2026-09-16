# Election Automation

A collection of scripts to help with automation of SJC JCR elections (Executive, General and By-Elections).

Inputs:

* Positions, including descriptions (taken from the constitution)
* Restrictions (taken from the constitution)
* Data about this election
* (Optional) Candidates for this election

Outputs:

* .tex files for positions booklet/manifestos/notice of poll
* Text for emails
* Instructions for SU platform/nominations form

## Setup

[Install python](https://python.org)

Run

`pip install -r requirements.txt`

Optional (if you want to compile latex locally):

* [Install tex-live](https://www.tug.org/texlive/) (this takes about an hour)
* If using VSCode, install the [latex workshop extension](https://github.com/James-Yu/LaTeX-Workshop)

If you do not want to compile latex locally, you can use [overleaf](https://overleaf.com).

Optional (if you want schema checking):

* copy [settings-template.json](settings-template.json) to [.vscode/settings.json](.vscode/settings.json)

Optional (if you want to use the browser agent):

Install playwright by above

Install the browsers:

`playwright install`

## Run

This section goes into detailed information on how to use the
various tools provided.

### Input data

Choose an `ELECTION_ABBREVIATION`.

The file containing the data for the election should be at `elections/election-{ELECTION_ABBREVIATION}.json` (or `.jsonc`).

You can copy a template to save information, or create this fully from scratch.

Some data is required, but much is not.
The schema for this elections file is located at [election.schema.json](automation/schemas/election.schema.json).

Change the election abbreviation (and file extension if needed) in [automation/scripts/election_abbr.py](automation/scripts/election_abbr.py).

If you have candidates, put them in `elections/candidates-{ELECTION_ABBREVIATION}` ([schema](automation/schemas/candidates.schema.json)).
Put their photo and manifesto in the folder `elections/{ELECTION_ABBREVIATION}-candidates`,
and make sure the file names match what you have written in the candidates file.
Convert formatting to LaTeX formatting for the LaTeX file (.tex file extension).
Note: the system needs a copy of the manifesto as a text file (for putting in the SU system) and as LaTeX
(for manifestos booklet).

### Data files

To run the scripts for creating files form data, run `python3 ./automation/scripts/data_filler.py`.

This will tell you which files were created, and which templates were skipped.
Templates are skipped when there is insufficient data to fill them.

### SU Platform

To run the files to input data on the SU platform, change the string `MODE` in [su-browser-agent.py](automation/scripts/su_browser_agent.py).

Update Monday First Week if needed.

If you are not at St John's JCR, you'll need to change the `ORGANISATION_ID` - you can get this as the number after `https://www.oxfordsu.org/organisation/6408/`, where this is the page for your organisation (which is the place where you send members to vote).

#### Creation

`MODE = "CREATE"`

* You need to log-in, using your SSO, and then press enter in the terminal.

If it fails, then either some data is missing, or the SU website layout changed.

The browser will wait for a small amount of time after creation.

#### Positions

`MODE = "POSITIONS"`

* Note: for this, you need the candidates (this is so you only create positions for those posts with candidates to save you the work)
* You need to log-in, using your SSO, find the election number:
  * Do this by changing to your organisation if needed
  * Then click on the election (in the list of elections)
  * You should get a URL like `https://www.oxfordsu.org/admin/elections/election/6408/2237/`
  * The number is `2237` (where `6408` is St John's JCR organisation id)
* Then type this into the terminal and press enter.

* For each position, due to intricacies of the SU website, you will need to follow the instructions in the terminal to do some manual work

#### Candidates

`MODE = "CANDIDATES"`

* Log-in, using your SSO, get the number (it is the same one as above), and type this into the terminal and press enter.

## Positions and Restrictions

Positions and Restrictions: copy from the constitution.

For positions, each line becomes a item in a list, but
sublists need to be separately formatted (using LaTeX).

Restrictions: put on a single line, and format (using LaTeX).
