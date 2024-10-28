package main

import (
	"bufio"
	"compress/gzip"
	"flag"
	"fmt"
	"os"
	"runtime"
	"strings"
	sync "sync"
)

type FastqRecord struct {
	head string
	seq  string
	plus string
	qual string
}

func parseFastqRecord(scanner *bufio.Scanner) (FastqRecord, bool) {
	if !scanner.Scan() {
		return FastqRecord{}, false
	}
	head := scanner.Text()
	if !scanner.Scan() {
		return FastqRecord{}, false
	}
	seq := scanner.Text()
	if !scanner.Scan() {
		return FastqRecord{}, false
	}
	plus := scanner.Text()
	if !scanner.Scan() {
		return FastqRecord{}, false
	}
	qual := scanner.Text()
	return FastqRecord{head, seq, plus, qual}, true
}

func processRecord(record FastqRecord) (FastqRecord, bool) {
	lastPos := strings.LastIndex(record.seq[:20], "TATAGGG")
	if lastPos == -1 {
		return FastqRecord{}, false
	}
	// Remove the longest matching segment including all TATAGGG in the first 20 bases
	for {
		nextPos := strings.LastIndex(record.seq[:lastPos], "TATAGGG")
		if nextPos == -1 {
			break
		}
		lastPos = nextPos
	}
	return FastqRecord{
		head: record.head,
		seq:  record.seq[lastPos+7:],
		plus: record.plus,
		qual: record.qual[lastPos+7:],
	}, true
}

func worker(records <-chan FastqRecord, results chan<- FastqRecord, wg *sync.WaitGroup) {
	defer wg.Done()
	for record := range records {
		if processedRecord, ok := processRecord(record); ok {
			results <- processedRecord
		}
	}
}

func main() {
	inputFile := flag.String("i", "", "Input FASTQ file (gzip compressed)")
	outputFile := flag.String("o", "", "Output FASTQ file (gzip compressed)")
	threads := flag.Int("t", runtime.NumCPU(), "Number of threads to use")
	flag.Parse()

	if *inputFile == "" || *outputFile == "" {
		fmt.Println("Usage: -i <input.gz> -o <output.gz> [-t <threads>]")
		os.Exit(1)
	}

	inFile, err := os.Open(*inputFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error opening input file: %v\n", err)
		os.Exit(1)
	}
	defer inFile.Close()

	gzipReader, err := gzip.NewReader(inFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating gzip reader: %v\n", err)
		os.Exit(1)
	}
	defer gzipReader.Close()

	scanner := bufio.NewScanner(gzipReader)
	bufSize := 4 * 1024 * 1024 // 4MB buffer size to improve performance
	scanner.Buffer(make([]byte, bufSize), bufSize)

	outFile, err := os.Create(*outputFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating output file: %v\n", err)
		os.Exit(1)
	}
	defer outFile.Close()

	gzipWriter := gzip.NewWriter(outFile)
	defer gzipWriter.Close()

	writer := bufio.NewWriter(gzipWriter)
	defer writer.Flush()

	records := make(chan FastqRecord, *threads*8)
	results := make(chan FastqRecord, *threads*8)

	var wg sync.WaitGroup
	for i := 0; i < *threads; i++ {
		wg.Add(1)
		go worker(records, results, &wg)
	}

	go func() {
		wg.Wait()
		close(results)
	}()

	go func() {
		for {
			record, ok := parseFastqRecord(scanner)
			if !ok {
				break
			}
			records <- record
		}
		close(records)
	}()

	for result := range results {
		writer.WriteString(result.head + "\n")
		writer.WriteString(result.seq + "\n")
		writer.WriteString(result.plus + "\n")
		writer.WriteString(result.qual + "\n")
	}
}

