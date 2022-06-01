#!/usr/bin/env python3

'''
##genomes_data_fetch.py

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

'''
import sys
import re
import glob
import subprocess as sp
#from Bio import Entrez
from datetime import date
import os.path



def tokenize(filename):
	digits = re.compile(r'(\d+)')
	return tuple(int(token) if match else token
                 for token, match in
                 ((fragment, digits.search(fragment))
                  for fragment in digits.split(filename)))


def get_genomes(terms,nosra):

	print("Fetching NCBI genomes")
	p0=sp.Popen('esearch -db genome -query "%s[organism]" | efetch -format docsum | xtract -pattern DocumentSummary -tab "<||>" -def "N/A" -element Organism_Name TaxId Assembly_Name Assembly_Accession Project_Accession Status Number_of_Chromosomes Create_Date > genomes.txt' %terms,shell=True).wait()

	#Get all plants from assemblies:
	print("Fetching NCBI assemblies")
	p1=sp.Popen('esearch -db assembly -query "%s[organism]" | esummary | xtract -pattern DocumentSummary -tab "<||>" -def "N/A" -element SpeciesName Taxid AssemblyName AssemblyAccession BioprojectAccn assembly-status SubmitterOrganization LastUpdateDate > assemblies.txt' %terms,shell=True).wait()
	
	if nosra!="nosra":
		print("Fetching SRA data")
		p2=sp.Popen('esearch -db sra -query "wgs[strategy] AND %s[orgn] NOT metagenom* NOT chloroplast NOT mitochond* NOT cpDNA NOT mtDNA NOT methylat* NOT target-enriched" | esummary | xtract -pattern DocumentSummary -tab "<||>" -def "N/A" -element Organism@taxid -element Organism@ScientificName -element Run@acc -element Submitter@center_name -element Platform -element UpdateDate >srr.txt' %terms,shell=True).wait()
	else:
		print("Skipping SRA")
	
	
	#Tabs can be used inside fields, therefore change sep to "<||>".

	p2=sp.Popen("sed -i 's/\t/,/g' assemblies.txt",shell=True).wait()

	p3=sp.Popen("sed -i 's/<||>/\t/g' assemblies.txt",shell=True).wait()

	p4=sp.Popen("sed -i 's/\t/,/g' genomes.txt",shell=True).wait()

	p5=sp.Popen("sed -i 's/<||>/\t/g' genomes.txt",shell=True).wait()
	
	p6=sp.Popen("sed -i 's/\t/,/g' plants_srr.txt",shell=True).wait()

	p7=sp.Popen("sed -i 's/<||>/\t/g' plants_srr.txt",shell=True).wait()
	


def parse_genomes():#get the complete of most recent genome for each taxid
	
	print("Parsing genome data")
	
	genomes={}
	
	f1=open("genomes.txt",'r')
	
	for x in f1:
		k=x.rstrip("\n").split("\t")
		name1=k[0]
		tax=k[1]
		acc=k[3]
		prj=k[4]
		status=k[5]
		nchrom=k[6]
		d=k[7].split(" ")[0].split("/")
		
		#print(x)
		
		cdate=date(int(d[0]),int(d[1]),int(d[2]))
	
		if tax not in genomes.keys():
			genomes[tax]={}
			genomes[tax]['name']=name1
			genomes[tax]['acc']=acc
			genomes[tax]['prj']=prj
			genomes[tax]['status']=status
			genomes[tax]['nchrom']=nchrom
			genomes[tax]['date']=cdate
			
		else:
			if genomes[tax]['status']=='Draft' and status=='Complete': #replace existing if new is better
		
				genomes[tax]['name']=name1
				genomes[tax]['acc']=acc
				genomes[tax]['prj']=prj
				genomes[tax]['status']=status
				genomes[tax]['nchrom']=nchrom
				genomes[tax]['date']=cdate
			
			if genomes[tax]['date']<cdate: #any other status, take most recent
				
				genomes[tax]['name']=name1
				genomes[tax]['acc']=acc
				genomes[tax]['prj']=prj
				genomes[tax]['status']=status
				genomes[tax]['nchrom']=nchrom
				genomes[tax]['date']=cdate
	
	f1.close()				
	return genomes

def parse_assemblies():

	print("Parsing assembly data")
	
	assemblies={}
	
	f1=open("assemblies.txt",'r')
	
	for x in f1:
		#print(x)
		k=x.rstrip("\n").split("\t")
		name1=k[0]
		tax=k[1]
		ass_name=k[2]
		acc=k[3]
		prj=k[4]
		status=k[5]
		org=k[6]
		d=k[7].split(" ")[0].split("/")
		
		#print(x)
		
		cdate=date(int(d[0]),int(d[1]),int(d[2]))
	
		if tax not in assemblies.keys():
			assemblies[tax]={}
			assemblies[tax]['name']=name1
			assemblies[tax]['acc']=acc
			assemblies[tax]['prj']=prj
			assemblies[tax]['status']=status
			assemblies[tax]['ass_name']=ass_name
			assemblies[tax]['org']=org
			assemblies[tax]['date']=cdate
			
		else:
			if assemblies[tax]['status']=='Contig' and status=='Scaffold': #replace existing if new is better
		
				assemblies[tax]['name']=name1
				assemblies[tax]['acc']=acc
				assemblies[tax]['prj']=prj
				assemblies[tax]['status']=status
				assemblies[tax]['ass_name']=ass_name
				assemblies[tax]['org']=org
				assemblies[tax]['date']=cdate
			
			if assemblies[tax]['status']=='Scaffold' and status=='Chromosome': #replace existing if new is better
		
				assemblies[tax]['name']=name1
				assemblies[tax]['acc']=acc
				assemblies[tax]['prj']=prj
				assemblies[tax]['status']=status
				assemblies[tax]['ass_name']=ass_name
				assemblies[tax]['org']=org
				assemblies[tax]['date']=cdate
			
			
			#####nope fix
			if assemblies[tax]['status']==status and assemblies[tax]['date']<cdate: #any other status, take most recent
				
				assemblies[tax]['name']=name1
				assemblies[tax]['acc']=acc
				assemblies[tax]['prj']=prj
				assemblies[tax]['status']=status
				assemblies[tax]['ass_name']=ass_name
				assemblies[tax]['org']=org
				assemblies[tax]['date']=cdate
	
	f1.close()				
	return assemblies

def parse_sra():

	print("Parsing sra data")
	
	sra={}
	
	f1=open("srr.txt",'r')
	
	for x in f1:
		#print(x)
		k=x.rstrip("\n").split("\t")
		name1=k[1]
		tax=k[0]
		acc=k[2]
		centre=k[3]
		inst=k[4]
		d=k[5].split(" ")[0].split("/")
		
		cdate=date(int(d[0]),int(d[1]),int(d[2]))
	
		if tax not in sra.keys():
			sra[tax]={}
			sra[tax]['name']=name1
			sra[tax]['acc']=acc
			sra[tax]['centre']=centre
			sra[tax]['inst']=inst
			sra[tax]['date']=cdate
			
		else:
			
			if sra[tax]['date']<cdate: #any other status, take most recent
				
				sra[tax]={}
				sra[tax]['name']=name1
				sra[tax]['acc']=acc
				sra[tax]['centre']=centre
				sra[tax]['inst']=inst
				sra[tax]['date']=cdate
			
			if sra[tax]['date']==cdate and sra[tax]['acc']=="N/A": #get other sample of same date if acc missing
				
				sra[tax]={}
				sra[tax]['name']=name1
				sra[tax]['acc']=acc
				sra[tax]['centre']=centre
				sra[tax]['inst']=inst
				sra[tax]['date']=cdate
			
	f1.close()				
	return sra
		
			
def getlocaldata(localdbfile,terms):

	#open tax2lin.txt
	#species2taxid={}
	data={}
	
	
	t1=open(localdbfile,'r')
	
	for x in t1:
		#print(x)
		tax1=x.split("\t")[0]
		#spec1=x.split("\t")[1].split(";")[-1].rstrip("\n")
		lin1=x.split("\t")[1].rstrip("\n")
		#species2taxid[spec1]=tax1
		data[tax1]=terms+";"+lin1
		
	t1.close()

	return(data)



def main():	
	
	terms=sys.argv[2]
	nosra=sys.argv[4]
	if sys.argv[1]=='update': #if no update then use existing files: genomes.txt assemblies.txt plants_srr.txt
		get_genomes(terms,nosra)
	
	#get taxonomy db
	localdbfile=sys.argv[3]
	
	tax2lin=getlocaldata(localdbfile,terms)
	
	
	genomes=parse_genomes()
	
	print(len(genomes),'genomes found')
	
	assemblies=parse_assemblies()
	
	print(len(assemblies),'assemblies found')
	
	if nosra!="nosra":
	
		sra=parse_sra()

		print(len(sra),'sra found')

		print("Adding full taxonomies")
		
			
	c=0
	for x in genomes.keys():
		c=c+1
		print('Adding genome taxonomy',c,end="\r")
		
		if x in tax2lin.keys():
			genomes[x]['lineage']=tax2lin[x]
		else:
			genomes[x]['lineage']="no lineage found"
			
	print("\n")
	
	c=0
	for x in assemblies.keys():
		c=c+1
		print('Adding assembly taxonomy',c,end="\r")
		if x in tax2lin.keys():
			assemblies[x]['lineage']=tax2lin[x]
		else:
			assemblies[x]['lineage']="no lineage found"	

	print("\n")
	
	if nosra!="nosra":
		c=0
		for x in sra.keys():
			c=c+1
			print('Adding sra taxonomy',c,end="\r")
			if x in tax2lin.keys():
				sra[x]['lineage']=tax2lin[x]
			else:
				sra[x]['lineage']="no lineage found"			

		print("\n")	
	
	#save data
	
	print("Saving results")
	
	genomefields=['name','acc','prj','status','nchrom','date','lineage']

	assemblyfields=['name','acc','prj','status','ass_name','org','date','lineage']

	srafields=['name','acc','centre','inst','date','lineage']
	
	g=open("genome_results.txt",'w')
	g.write("TaxID\tSpecies\tAccession\tProject\tStatus\tNumChromosomes\tDate\tFull_Taxonomy\n")
	for x in genomes.keys():
		g.write(x)
		for y in genomefields:
			g.write("\t"+str(genomes[x][y]))	
		g.write("\n")
	g.close()
	
	g=open("assembly_results.txt",'w')
	g.write("TaxID\tSpecies\tAccession\tProject\tStatus\tTitle\tOrganisation\tDate\tFull_Taxonomy\tGenome_present\n")
	for x in assemblies.keys():
		g.write(x)
		for y in assemblyfields:
			g.write("\t"+str(assemblies[x][y]))
		if x in genomes.keys():
			g.write("\ty")
		else:
			g.write("\tn")
		g.write("\n")
	g.close()
	
	if nosra!="nosra":
		g=open("sra_results.txt",'w')
		g.write("TaxID\tSpecies\tAccession\tOrganisation\tInstrument\tDate\tFull_Taxonomy\tGenome_present\tAssembly_present\n")
		for x in sra.keys():
			g.write(x)
			for y in srafields:
				g.write("\t"+str(sra[x][y]))	
			if x in genomes.keys():
				g.write("\ty")
			else:
				g.write("\tn")
			if x in assemblies.keys():
				g.write("\ty")
			else:
				g.write("\tn")		
			g.write("\n")
		g.close()

if __name__ == '__main__': main()


		