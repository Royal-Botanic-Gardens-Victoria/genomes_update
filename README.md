#genomes_data_fetch.py

T. R. Allnutt 2021. Collects all current green plant (or any other group you specify) genome data from NCBI. 

Requires taxonkit, https://github.com/Royal-Botanic-Gardens-Victoria/taxonkit. In order to make local taxonomy database. Install and add to PATH.

NCBI taxonomy must be downloaded, e.g.:

mkdir /g/data/nm31/db/taxonomy
cd /g/data/nm31/db/taxonomy
wget https://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz
tar -xvf new_taxdump.tar.gz

NCBI esearch must be installed. https://www.ncbi.nlm.nih.gov/books/NBK179288/
An Entrez account and api key is required
Set NCBI variables in ~/.bash_profile (https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/):
export NCBI_API_KEY=<your_key>
export NCBI_EMAIL=<your_email>

taxonkit requires the TAXONKIT_DB variable to be set - add to ~/.bash_profile or ~/.profile:

export TAXONKIT_DB=/g/data/nm31/db/taxonomy/

Make local taxid / lineage database:

grep "Viridiplantae" /g/data/nm31/db/taxonomy/fullnamelineage.dmp | cut -f1 | taxonkit lineage | taxonkit reformat -a -f "{p};{c};{o};{f};{g};{s}" | cut -f 1,3 |sed ':a;N;$!ba;s/;\n/\n/g' > lineage.default

Change "Viridiplantae" to any other taxonomic group of interest, e.g. 'Fungi'.

Usage (all arguments positional):
genomes_data_fetch.py update "Viridiplantae" sra

SRA search can take a long time (>1 hour), to skip use 'nosra' argument.
