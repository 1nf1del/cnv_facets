#!/usr/bin/env python

import unittest
import shutil
import os
import subprocess as sp
import sys
import gzip
import re

def vcf_to_list(vcf_file):
    vcf= []
    with gzip.open(vcf_file) as gz:
        for line in gz:
            vcf.append(line.decode())
    return vcf

class cnv_facets(unittest.TestCase):

    def setUp(self):
        sys.stderr.write('\n' + self.id().split('.')[-1] + ' ') # Print test name
        if os.path.exists('test_out'):
            shutil.rmtree('test_out')

    def tearDown(self):
        if os.path.exists('test_out'):
            shutil.rmtree('test_out')

    def testShowHelp(self):
        p = sp.Popen("../bin/cnv_facets.R --help", shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self.assertTrue('--tumour', stderr.decode())
        
    def testCompressedPileupInput(self):
        p = sp.Popen("../bin/cnv_facets.R -p data/pileup.csv.gz -o test_out/out", shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self.assertTrue(os.path.exists('test_out/out.vcf.gz'))
        self.assertTrue(os.path.exists('test_out/out.cnv.png'))
        self.assertTrue(os.path.exists('test_out/out.spider.pdf'))

    def testUncompressedPileupInput(self):
        p = sp.Popen("../bin/cnv_facets.R -p data/pileup.csv -o test_out/out", shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self.assertTrue(os.path.exists('test_out/out.vcf.gz'))
        self.assertTrue(os.path.exists('test_out/out.cnv.png'))
        self.assertTrue(os.path.exists('test_out/out.spider.pdf'))

    def testBamInput(self):
        p = sp.Popen("../bin/cnv_facets.R -t data/tumour.bam -n data/normal.bam -vcf data/snps.vcf.gz -o test_out/out", shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self.assertTrue(os.path.exists('test_out/out.vcf.gz'))
        self.assertTrue(os.path.exists('test_out/out.cnv.png'))
        self.assertTrue(os.path.exists('test_out/out.spider.pdf'))
        self.assertTrue(os.path.exists('test_out/out.csv.gz'))

    def testRealDataset(self):
        p = sp.Popen("../bin/cnv_facets.R -p data/stomach.csv.gz -o test_out/out", shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self.assertTrue(os.path.exists('test_out/out.vcf.gz'))
        self.assertTrue(os.path.exists('test_out/out.cnv.png'))
        self.assertTrue(os.path.exists('test_out/out.spider.pdf'))

    def testEnsemblChromsomes(self):
        p = sp.Popen("../bin/cnv_facets.R -p data/stomach.csv.gz -o test_out/out", shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        
        vcf= vcf_to_list('test_out/out.vcf.gz')

        self.assertTrue('##contig=<ID=1>' in ''.join(vcf))
        self.assertTrue('##contig=<ID=X>' in ''.join(vcf))
        self.assertTrue( not '##contig=<ID=chrX>' in ''.join(vcf))
        self.assertTrue( not '##contig=<ID=chr23>' in ''.join(vcf))
        self.assertTrue( not '##contig=<ID=23>' in ''.join(vcf))
        
        self.assertTrue(vcf[-1].startswith('X\t'))

        for rec in vcf:
            self.assertTrue( not rec.startswith('23\t'))
        
    def testUcscChromsomes(self):
        p = sp.Popen("../bin/cnv_facets.R -p data/stomach_chr.csv.gz -o test_out/out", shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        
        vcf= vcf_to_list('test_out/out.vcf.gz')

        self.assertTrue('##contig=<ID=chr1>' in ''.join(vcf))
        self.assertTrue('##contig=<ID=chrX>' in ''.join(vcf))
        self.assertTrue( not '##contig=<ID=X>' in ''.join(vcf))
        self.assertTrue( not '##contig=<ID=chr23>' in ''.join(vcf))
        self.assertTrue( not '##contig=<ID=23>' in ''.join(vcf))
        
        self.assertTrue(vcf[-1].startswith('chrX\t'))

        for rec in vcf:
            self.assertTrue(rec.startswith('chr'))
            self.assertTrue( not rec.startswith('chr23\t'))

    def testMouseGenome(self):
        p = sp.Popen("../bin/cnv_facets.R -p data/stomach_chr.csv.gz -o test_out/out -g mm10", shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        
        vcf= vcf_to_list('test_out/out.vcf.gz')
        
        self.assertTrue(vcf[-1].startswith('chrX\t'))
        self.assertTrue('chr19' in ''.join(vcf))

        for rec in vcf:
            self.assertTrue( not rec.startswith('chr20\t'))
            self.assertTrue( not rec.startswith('chr21t'))
            self.assertTrue( not rec.startswith('chr22\t'))

    def testAnnotation(self):
        p = sp.Popen("../bin/cnv_facets.R -p data/stomach_chr.csv.gz -o test_out/out --annotation data/annotation.bed", shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        
        vcf= vcf_to_list('test_out/out.vcf.gz')

        self.assertTrue('chr1\t69' in ''.join(vcf))

        for rec in vcf:
            if not rec.startswith('#'):
                self.assertTrue('CNV_ANN' in rec)
            
            if rec.startswith('chr1\t69'):
                # Multiple genes assigned to the same CNV
                self.assertTrue('C,A,B,gene%3Db%3BGene%2CFoo' in rec)
            
            if 'NEUTR' in rec:
                self.assertTrue('CNV_ANN=.' in rec)

        # "chr1"  69424   29651737    29582314    "*" 1   2857    194 0.517842798839592   0.273388531519885   10  0.496188540216101   0.374823190128964   0.890513462888664   3   1   "DUP"   "C,A,B,gene%3Db%3BGene%2CFoo"    

if __name__ == '__main__':
    unittest.main()
