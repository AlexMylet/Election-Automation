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

## Run

Change the election abbreviation in [automation/scripts/election_abbr.py](automation/scripts/election_abbr.py).

Copy a template to (or create yours at) elections/election-{ELECTION_ABBREVIATION}.

If you have candidates, put them in elections/candidates-{ELECTION_ABBREVIATION}.
Put data about them in the folder elections/{ELECTION_ABBREVIATION}-candidates,
and make sure the file names match.
Convert formatting to LaTeX formatting for the LaTeX file.

To run the scripts, run `python3 ./automation/scripts/data_filler.py`.

## Positions and Restrictions

Positions and Restrictions: copy from the constitution.

For positions, each line becomes a item in a list, but
sublists need to be separately formatted (using LaTeX).

Restrictions: put on a single line, and format (using LaTeX).
