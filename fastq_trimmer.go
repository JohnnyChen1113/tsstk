package main

import (
    "bufio"
    "compress/gzip"
    "flag"
    "fmt"
    "io"
    "os"
    "strings"
    "sync"
)

// Performance-related constants
const (
    maxScanTokenSize  = 8 * 1024 * 1024 // 8MB
    batchSize         = 1000            // Batch processing size
    channelBufferSize = 1000            // Channel buffer size
)

// Object pool for FastqRecord
var fastqRecordPool = sync.Pool{
    New: func() interface{} {
        return &FastqRecord{}
    },
}

type FastqRecord struct {
    head string
    seq  string
    plus string
    qual string
}

// Fixed parsePairedFastqRecord function
func parsePairedFastqRecord(scanner1, scanner2 *bufio.Scanner) (FastqRecord, FastqRecord, bool) {
    if !scanner1.Scan() || !scanner2.Scan() {
        return FastqRecord{}, FastqRecord{}, false
    }
    head1, head2 := scanner1.Text(), scanner2.Text()
    if !strings.HasPrefix(head1, "@") || head1[1:] != head2[1:] {
        fmt.Fprintf(os.Stderr, "Unmatched pair: %s vs %s\n", head1, head2)
        os.Exit(1)
    }

    if !scanner1.Scan() || !scanner2.Scan() {
        return FastqRecord{}, FastqRecord{}, false
    }
    seq1, seq2 := scanner1.Text(), scanner2.Text()

    if !scanner1.Scan() || !scanner2.Scan() {
        return FastqRecord{}, FastqRecord{}, false
    }
    plus1, plus2 := scanner1.Text(), scanner2.Text()

    if !scanner1.Scan() || !scanner2.Scan() {
        return FastqRecord{}, FastqRecord{}, false
    }
    qual1, qual2 := scanner1.Text(), scanner2.Text()

    return FastqRecord{head1, seq1, plus1, qual1}, FastqRecord{head2, seq2, plus2, qual2}, true
}

func processPairedRecord(record1, record2 FastqRecord) (FastqRecord, FastqRecord, bool) {
    lastPos := strings.LastIndex(record1.seq[:20], "TATAGGG")
    if lastPos == -1 {
        return FastqRecord{}, FastqRecord{}, false
    }
    // Trim R1 starting from the position after the last "TATAGGG"
    trimmedSeq1 := record1.seq[lastPos+7:]
    trimmedQual1 := record1.qual[lastPos+7:]

    // R2 remains unchanged
    return FastqRecord{
        head: record1.head,
        seq:  trimmedSeq1,
        plus: record1.plus,
        qual: trimmedQual1,
    }, record2, true
}

// Batch processing version of pairedWorker
func pairedWorker(records <-chan [][2]FastqRecord, results chan<- [2]FastqRecord, wg *sync.WaitGroup) {
    defer wg.Done()
    for batch := range records {
        for _, pair := range batch {
            record1, record2 := pair[0], pair[1]
            if processed1, processed2, ok := processPairedRecord(record1, record2); ok {
                results <- [2]FastqRecord{processed1, processed2}
            }
        }
    }
}

// Create optimized Scanner
func createScanner(reader io.Reader) *bufio.Scanner {
    scanner := bufio.NewScanner(reader)
    buf := make([]byte, maxScanTokenSize)
    scanner.Buffer(buf, maxScanTokenSize)
    return scanner
}

func printHelp() {
    fmt.Println("Usage:")
    fmt.Println("  -input <file>         Input file for single-end data")
    fmt.Println("  -inputR1 <file>       Input file for paired-end data R1")
    fmt.Println("  -inputR2 <file>       Input file for paired-end data R2")
    fmt.Println("  -outputR1 <file>      Output file for paired-end data R1")
    fmt.Println("  -outputR2 <file>      Output file for paired-end data R2")
    fmt.Println("  -threads <number>     Number of threads to use")
}

func main() {
    inputFile := flag.String("input", "", "Input file for single-end data")
    inputFileR1 := flag.String("inputR1", "", "Input file for paired-end data R1")
    inputFileR2 := flag.String("inputR2", "", "Input file for paired-end data R2")
    outputFileR1 := flag.String("outputR1", "", "Output file for paired-end data R1")
    outputFileR2 := flag.String("outputR2", "", "Output file for paired-end data R2")
    threads := flag.Int("threads", 1, "Number of threads to use")
    flag.Parse()

    if *inputFile != "" {
        // Single-end data processing logic (to be implemented)
        fmt.Println("Processing single-end data...")
    } else if *inputFileR1 != "" && *inputFileR2 != "" {
        fmt.Println("Processing paired-end data...")

        // Open input files
        r1File, err := os.Open(*inputFileR1)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error opening R1 file: %v\n", err)
            os.Exit(1)
        }
        defer r1File.Close()

        r2File, err := os.Open(*inputFileR2)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error opening R2 file: %v\n", err)
            os.Exit(1)
        }
        defer r2File.Close()

        // Create output files
        w1File, err := os.Create(*outputFileR1)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error creating output R1 file: %v\n", err)
            os.Exit(1)
        }
        defer w1File.Close()

        w2File, err := os.Create(*outputFileR2)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error creating output R2 file: %v\n", err)
            os.Exit(1)
        }
        defer w2File.Close()

        // Create gzip readers and writers
        r1Reader, err := gzip.NewReader(r1File)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error creating gzip reader for R1: %v\n", err)
            os.Exit(1)
        }
        defer r1Reader.Close()

        r2Reader, err := gzip.NewReader(r2File)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error creating gzip reader for R2: %v\n", err)
            os.Exit(1)
        }
        defer r2Reader.Close()

        w1Writer := gzip.NewWriter(w1File)
        defer w1Writer.Close()
        w2Writer := gzip.NewWriter(w2File)
        defer w2Writer.Close()

        // Create optimized scanners
        scanner1 := createScanner(r1Reader)
        scanner2 := createScanner(r2Reader)

        // Create channels
        records := make(chan [][2]FastqRecord, channelBufferSize)
        results := make(chan [2]FastqRecord, channelBufferSize)

        // Start worker goroutines
        var wg sync.WaitGroup
        for i := 0; i < *threads; i++ {
            wg.Add(1)
            go pairedWorker(records, results, &wg)
        }

        // Start result processing goroutine
        go func() {
            for result := range results {
                fmt.Fprintf(w1Writer, "%s\n%s\n%s\n%s\n", 
                    result[0].head, result[0].seq, result[0].plus, result[0].qual)
                fmt.Fprintf(w2Writer, "%s\n%s\n%s\n%s\n", 
                    result[1].head, result[1].seq, result[1].plus, result[1].qual)
            }
        }()

        // Read and send batch data
        batch := make([][2]FastqRecord, 0, batchSize)
        for {
            record1, record2, ok := parsePairedFastqRecord(scanner1, scanner2)
            if !ok {
                break
            }
            batch = append(batch, [2]FastqRecord{record1, record2})
            if len(batch) >= batchSize {
                records <- batch
                batch = make([][2]FastqRecord, 0, batchSize)
            }
        }
        if len(batch) > 0 {
            records <- batch
        }

        close(records)
        wg.Wait()
        close(results)
    } else {
        fmt.Println("Error: Invalid input configuration")
        printHelp()
        os.Exit(1)
    }
}

