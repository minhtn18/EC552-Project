from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from blast_database import inspect_database, preview_database_fasta
from Blast_code import (
    DEFAULT_DATABASE_NAME,
    add_fasta_to_blast_database,
    add_sequence_to_blast_database,
    build_blast_database,
    build_blast_database_from_sequence,
    parse_blast_tabular,
    read_fasta,
    resolve_database_prefix,
    run_blastn,
    run_blastn_from_sequence,
)
from disease_database_tools import (
    DEFAULT_DISEASE_FASTA,
    add_snp_record_to_database,
    merge_snp_fasta_into_database,
    preview_disease_database,
    summarize_disease_database,
)
from snp_analysis import analyze_with_disease_fasta


class BlastApp:
    DISEASE_HEADER_TEMPLATE = (
        "VariantLabel|gene=GENE|variant=c.POSREF>ALT|ref_pos=POS|ref=REF|alt=ALT|"
        "pathogenicity=Unknown|harm=Unknown|disease=Disease_name"
    )

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("BLAST GUI")
        self.root.geometry("900x700")

        self.blast_bin_var = tk.StringVar()
        self.add_fasta_var = tk.StringVar()
        self.add_header_var = tk.StringVar()
        self.disease_fasta_var = tk.StringVar()
        self.disease_header_var = tk.StringVar()
        self.query_var = tk.StringVar()
        self.query_header_var = tk.StringVar(value="user_query")
        self.db_name_var = tk.StringVar(value=DEFAULT_DATABASE_NAME)
        self.results_var = tk.StringVar(value="results.txt")
        self.status_var = tk.StringVar(value="Ready")

        self._build_layout()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        main = ttk.Frame(canvas, padding=12)
        canvas_window = canvas.create_window((0, 0), window=main, anchor="nw")

        def _update_scroll_region(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _resize_embedded_frame(event) -> None:
            canvas.itemconfigure(canvas_window, width=event.width)

        main.bind("<Configure>", _update_scroll_region)
        canvas.bind("<Configure>", _resize_embedded_frame)

        def _on_mousewheel(event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self._add_path_row(main, "BLAST bin folder", self.blast_bin_var, self.pick_blast_bin, 0)
        ttk.Label(main, text="BLAST database name or prefix").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(main, textvariable=self.db_name_var, width=40).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(main, text="Browse", command=self.pick_database_prefix).grid(row=1, column=2, padx=4, pady=4)

        self._add_path_row(main, "FASTA to add to database", self.add_fasta_var, self.pick_add_fasta, 2)

        db_button_frame = ttk.Frame(main)
        db_button_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)
        ttk.Button(db_button_frame, text="Create DB From FASTA", command=self.create_database_from_fasta).pack(side="left", padx=4)
        ttk.Button(db_button_frame, text="Add FASTA To Database", command=self.add_fasta_to_database).pack(side="left", padx=4)
        ttk.Button(db_button_frame, text="Preview Database", command=self.preview_database).pack(side="left", padx=4)

        ttk.Label(main, text="Database entry header").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(main, textvariable=self.add_header_var, width=40).grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(main, text="Database entry sequence").grid(row=5, column=0, sticky="nw", pady=4)
        self.add_sequence_text = tk.Text(main, height=5, width=70)
        self.add_sequence_text.grid(row=5, column=1, columnspan=2, sticky="nsew", pady=4)
        self._add_text_scrollbar(main, self.add_sequence_text, row=5, column=3)

        add_sequence_button_frame = ttk.Frame(main)
        add_sequence_button_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=6)
        ttk.Button(add_sequence_button_frame, text="Create DB From Header/Sequence", command=self.create_database_from_sequence).pack(side="left", padx=4)
        ttk.Button(add_sequence_button_frame, text="Add Header/Sequence To Database", command=self.add_sequence_record_to_database).pack(side="left", padx=4)

        self._add_path_row(main, "Query FASTA (optional)", self.query_var, self.pick_query, 7)

        ttk.Label(main, text="Query header").grid(row=8, column=0, sticky="w", pady=4)
        ttk.Entry(main, textvariable=self.query_header_var, width=40).grid(row=8, column=1, sticky="ew", pady=4)

        ttk.Label(main, text="Query sequence (paste DNA here)").grid(row=9, column=0, sticky="nw", pady=4)
        self.query_sequence_text = tk.Text(main, height=6, width=70)
        self.query_sequence_text.grid(row=9, column=1, columnspan=2, sticky="nsew", pady=4)
        self._add_text_scrollbar(main, self.query_sequence_text, row=9, column=3)

        ttk.Label(main, text="BLAST results file (.txt/.tsv)").grid(row=10, column=0, sticky="w", pady=4)
        ttk.Entry(main, textvariable=self.results_var, width=40).grid(row=10, column=1, sticky="ew", pady=4)
        results_button_frame = ttk.Frame(main)
        results_button_frame.grid(row=10, column=2, padx=4, pady=4, sticky="w")
        ttk.Button(results_button_frame, text="Open", command=self.pick_existing_results_file).pack(side="left", padx=(0, 4))
        ttk.Button(results_button_frame, text="Save As", command=self.pick_results_file).pack(side="left")

        button_frame = ttk.Frame(main)
        button_frame.grid(row=11, column=0, columnspan=3, sticky="ew", pady=10)
        ttk.Button(button_frame, text="Run BLAST", command=self.run_blast).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Show Parsed Results", command=self.show_results).pack(side="left", padx=4)
        self.show_snp_button = ttk.Button(button_frame, text="Show SNP Analysis", command=self.show_snp_analysis)
        self.show_snp_button.pack(side="left", padx=4)

        ttk.Label(main, text="Status").grid(row=12, column=0, sticky="w", pady=4)
        ttk.Label(main, textvariable=self.status_var).grid(row=12, column=1, columnspan=2, sticky="w", pady=4)

        ttk.Separator(main, orient="horizontal").grid(row=13, column=0, columnspan=3, sticky="ew", pady=10)

        self._add_path_row(main, "Disease SNP FASTA", self.disease_fasta_var, self.pick_disease_fasta, 14)
        self.disease_fasta_var.set(str(DEFAULT_DISEASE_FASTA))

        disease_button_frame = ttk.Frame(main)
        disease_button_frame.grid(row=15, column=0, columnspan=3, sticky="ew", pady=6)
        ttk.Button(disease_button_frame, text="Preview Disease DB", command=self.preview_disease_db).pack(side="left", padx=4)
        ttk.Button(disease_button_frame, text="Add Disease FASTA", command=self.add_disease_fasta_to_db).pack(side="left", padx=4)
        ttk.Button(disease_button_frame, text="Show Disease Template", command=self.show_disease_template).pack(side="left", padx=4)

        ttk.Label(main, text="Disease entry header").grid(row=16, column=0, sticky="w", pady=4)
        ttk.Entry(main, textvariable=self.disease_header_var, width=40).grid(row=16, column=1, sticky="ew", pady=4)
        ttk.Button(main, text="Use Template", command=self.use_disease_template).grid(row=16, column=2, padx=4, pady=4, sticky="w")

        ttk.Label(main, text="Disease entry sequence").grid(row=17, column=0, sticky="nw", pady=4)
        self.disease_sequence_text = tk.Text(main, height=5, width=70)
        self.disease_sequence_text.grid(row=17, column=1, columnspan=2, sticky="nsew", pady=4)
        self._add_text_scrollbar(main, self.disease_sequence_text, row=17, column=3)

        disease_add_button_frame = ttk.Frame(main)
        disease_add_button_frame.grid(row=18, column=0, columnspan=3, sticky="ew", pady=6)
        ttk.Button(disease_add_button_frame, text="Add Disease Header/Sequence", command=self.add_disease_record_to_db).pack(side="left", padx=4)

        ttk.Label(main, text="Output").grid(row=19, column=0, sticky="nw", pady=4)
        self.output_text = tk.Text(main, height=18, width=90)
        self.output_text.grid(row=19, column=1, columnspan=2, sticky="nsew", pady=4)
        self._add_text_scrollbar(main, self.output_text, row=19, column=3)

        main.columnconfigure(1, weight=1)
        main.columnconfigure(2, weight=1)
        main.rowconfigure(19, weight=1)
        self.update_mode()

    def _add_path_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar, command, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable, width=60).grid(row=row, column=1, sticky="ew", pady=4)
        ttk.Button(parent, text="Browse", command=command).grid(row=row, column=2, padx=4, pady=4)

    def _add_text_scrollbar(self, parent: ttk.Frame, widget: tk.Text, row: int, column: int) -> None:
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=widget.yview)
        widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=row, column=column, sticky="ns", pady=4)

    def pick_blast_bin(self) -> None:
        folder = filedialog.askdirectory(title="Select BLAST bin folder")
        if folder:
            self.blast_bin_var.set(folder)

    def pick_query(self) -> None:
        path = filedialog.askopenfilename(title="Select query FASTA", filetypes=[("FASTA files", "*.fa *.fasta"), ("All files", "*.*")])
        if path:
            self.query_var.set(path)

    def pick_add_fasta(self) -> None:
        path = filedialog.askopenfilename(title="Select FASTA to add to database", filetypes=[("FASTA files", "*.fa *.fasta"), ("All files", "*.*")])
        if path:
            self.add_fasta_var.set(path)

    def pick_disease_fasta(self) -> None:
        path = filedialog.askopenfilename(title="Select disease SNP FASTA", filetypes=[("FASTA files", "*.fa *.fasta"), ("All files", "*.*")])
        if path:
            self.disease_fasta_var.set(path)

    def pick_database_prefix(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Choose BLAST database prefix",
            defaultextension="",
            filetypes=[("All files", "*.*")],
        )
        if path:
            self.db_name_var.set(path)

    def pick_results_file(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save BLAST results as",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("TSV files", "*.tsv"), ("All files", "*.*")],
        )
        if path:
            self.results_var.set(path)

    def pick_existing_results_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select existing BLAST results file",
            filetypes=[("Text files", "*.txt"), ("TSV files", "*.tsv"), ("All files", "*.*")],
        )
        if path:
            self.results_var.set(path)

    def run_blast(self) -> None:
        try:
            self._set_status("Running BLAST...")
            blast_bin = self.blast_bin_var.get().strip()
            db_name = self.db_name_var.get().strip()
            results_file = self.results_var.get().strip()
            query_file = self.query_var.get().strip()
            query_sequence = self.query_sequence_text.get("1.0", "end").strip()
            query_header = self.query_header_var.get().strip() or "user_query"
            self._require_inputs(blast_bin, db_name, results_file)
            resolved_db = resolve_database_prefix(db_name, blast_bin)
            self._write_output(f"Using database: {resolved_db}\n")

            if query_sequence:
                result = run_blastn_from_sequence(
                    query_sequence=query_sequence,
                    db_name=db_name,
                    output_file=results_file,
                    blast_bin=blast_bin,
                    query_header=query_header,
                )
            elif query_file:
                result = run_blastn(query_file, db_name, results_file, blast_bin)
            else:
                raise ValueError("Provide either a query FASTA file or paste a query sequence.")
            self._write_output(result.stdout or result.stderr or "BLAST run completed.\n")
            self._set_status("BLAST complete")
        except Exception as exc:
            self._set_status("BLAST failed")
            messagebox.showerror("BLAST Error", str(exc))

    def create_database_from_fasta(self) -> None:
        try:
            self._set_status("Creating database...")
            blast_bin = self.blast_bin_var.get().strip()
            db_name = self.db_name_var.get().strip()
            fasta_path = self.add_fasta_var.get().strip()
            self._require_inputs(blast_bin, db_name, fasta_path)
            resolved_db = resolve_database_prefix(db_name, blast_bin)
            self._write_output(f"Creating database: {resolved_db}\n")

            result = build_blast_database(
                reference_fasta=fasta_path,
                db_name=db_name,
                blast_bin=blast_bin,
            )
            self._write_output(result.stdout or result.stderr or "Database creation completed.\n")
            self._set_status("Database creation complete")
        except Exception as exc:
            self._set_status("Database creation failed")
            messagebox.showerror("Database Creation Error", str(exc))

    def add_fasta_to_database(self) -> None:
        try:
            self._set_status("Updating database...")
            blast_bin = self.blast_bin_var.get().strip()
            db_name = self.db_name_var.get().strip()
            fasta_path = self.add_fasta_var.get().strip()
            self._require_inputs(blast_bin, db_name, fasta_path)
            resolved_db = resolve_database_prefix(db_name, blast_bin)
            self._write_output(f"Updating database: {resolved_db}\n")

            result = add_fasta_to_blast_database(
                new_fasta=fasta_path,
                db_name=db_name,
                blast_bin=blast_bin,
            )
            merge_result = result["merge_result"]
            build_result = result["build_result"]
            summary = (
                f"Database updated from {result['source_fasta']}\n"
                f"Input records: {merge_result['input_count']}\n"
                f"Output records: {merge_result['output_count']}\n"
                f"Duplicates removed: {len(merge_result['duplicates_removed'])}\n"
            )
            self._write_output(summary)
            if build_result.stdout or build_result.stderr:
                self._write_output((build_result.stdout or build_result.stderr) + "\n")
            self._set_status("Database update complete")
        except Exception as exc:
            self._set_status("Database update failed")
            messagebox.showerror("Database Update Error", str(exc))

    def create_database_from_sequence(self) -> None:
        try:
            self._set_status("Creating database...")
            blast_bin = self.blast_bin_var.get().strip()
            db_name = self.db_name_var.get().strip()
            header = self.add_header_var.get().strip()
            sequence = self.add_sequence_text.get("1.0", "end").strip()
            self._require_inputs(blast_bin, db_name, header, sequence)
            resolved_db = resolve_database_prefix(db_name, blast_bin)
            self._write_output(f"Creating database: {resolved_db}\n")

            result = build_blast_database_from_sequence(
                reference_sequence=sequence,
                reference_header=header,
                db_name=db_name,
                blast_bin=blast_bin,
            )
            self._write_output(result.stdout or result.stderr or "Database creation completed.\n")
            self._set_status("Database creation complete")
        except Exception as exc:
            self._set_status("Database creation failed")
            messagebox.showerror("Database Creation Error", str(exc))

    def add_sequence_record_to_database(self) -> None:
        try:
            self._set_status("Updating database...")
            blast_bin = self.blast_bin_var.get().strip()
            db_name = self.db_name_var.get().strip()
            header = self.add_header_var.get().strip()
            sequence = self.add_sequence_text.get("1.0", "end").strip()
            self._require_inputs(blast_bin, db_name, header, sequence)
            resolved_db = resolve_database_prefix(db_name, blast_bin)
            self._write_output(f"Updating database: {resolved_db}\n")

            result = add_sequence_to_blast_database(
                header=header,
                sequence=sequence,
                db_name=db_name,
                blast_bin=blast_bin,
            )
            merge_result = result["merge_result"]
            build_result = result["build_result"]
            summary = (
                f"Database updated from entered sequence: {result['header']}\n"
                f"Input records: {merge_result['input_count']}\n"
                f"Output records: {merge_result['output_count']}\n"
                f"Duplicates removed: {len(merge_result['duplicates_removed'])}\n"
            )
            self._write_output(summary)
            if build_result.stdout or build_result.stderr:
                self._write_output((build_result.stdout or build_result.stderr) + "\n")
            self._set_status("Database update complete")
        except Exception as exc:
            self._set_status("Database update failed")
            messagebox.showerror("Database Update Error", str(exc))

    def preview_database(self) -> None:
        try:
            blast_bin = self.blast_bin_var.get().strip()
            db_name = self.db_name_var.get().strip()
            self._require_inputs(blast_bin, db_name)
            info = inspect_database(blast_bin=blast_bin, db_name=db_name)
            preview = preview_database_fasta(blast_bin=blast_bin, db_name=db_name)
            lines = [
                f"Database: {info['database']}",
                f"Record count: {info['record_count']}",
                "",
            ]
            for header in info["headers"]:
                lines.append(header)
            lines.append("")
            lines.append(preview)
            self._show_text_popup("Database Preview", "\n".join(lines))
        except Exception as exc:
            messagebox.showerror("Database Preview Error", str(exc))

    def preview_disease_db(self) -> None:
        try:
            disease_fasta = self.disease_fasta_var.get().strip() or str(DEFAULT_DISEASE_FASTA)
            summary = summarize_disease_database(disease_fasta)
            records = read_fasta(disease_fasta)
            summary_lines = [f"Disease database: {disease_fasta}", f"Record count: {len(summary)}", ""]
            for row in summary:
                summary_lines.append(f">{row['header']}")
                matching_record = next((record for record in records if record.header == row["header"]), None)
                if matching_record:
                    summary_lines.append(matching_record.sequence)
                summary_lines.append("")
            self._show_text_popup("Disease Database", "\n".join(summary_lines))
        except Exception as exc:
            messagebox.showerror("Disease Database Error", str(exc))

    def show_disease_template(self) -> None:
        template_text = (
            "Disease header template\n\n"
            f"{self.DISEASE_HEADER_TEMPLATE}\n\n"
            "Meaning:\n"
            "VariantLabel = short label for this disease/SNP record\n"
            "gene = gene symbol, for example HBB\n"
            "variant = variant notation, for example c.59T>C\n"
            "ref_pos = reference position as an integer\n"
            "ref = reference base\n"
            "alt = observed/patient base\n"
            "pathogenicity = Pathogenic / Likely_pathogenic / Benign / Unknown\n"
            "harm = High / Medium / Low / Unknown\n"
            "disease = disease name with underscores or simple text\n\n"
            "Example:\n"
            "HBB_custom|gene=HBB|variant=c.59T>C|ref_pos=59|ref=T|alt=C|"
            "pathogenicity=Likely_pathogenic|harm=Medium|disease=Your_disease_name"
        )
        self._show_text_popup("Disease Template", template_text)

    def use_disease_template(self) -> None:
        self.disease_header_var.set(self.DISEASE_HEADER_TEMPLATE)

    def add_disease_fasta_to_db(self) -> None:
        try:
            disease_fasta = self.disease_fasta_var.get().strip() or str(DEFAULT_DISEASE_FASTA)
            source_fasta = filedialog.askopenfilename(
                title="Select disease FASTA to merge",
                filetypes=[("FASTA files", "*.fa *.fasta"), ("All files", "*.*")],
            )
            if not source_fasta:
                return
            result = merge_snp_fasta_into_database([source_fasta], disease_fasta=disease_fasta)
            merge_result = result["merge_result"]
            self._write_output(
                f"Disease DB updated from {source_fasta}\n"
                f"Input records: {merge_result['input_count']}\n"
                f"Output records: {merge_result['output_count']}\n"
                f"Duplicates removed: {len(merge_result['duplicates_removed'])}\n"
            )
            self._set_status("Disease database update complete")
        except Exception as exc:
            self._set_status("Disease database update failed")
            messagebox.showerror("Disease Database Error", str(exc))

    def add_disease_record_to_db(self) -> None:
        try:
            disease_fasta = self.disease_fasta_var.get().strip() or str(DEFAULT_DISEASE_FASTA)
            header = self.disease_header_var.get().strip()
            sequence = self.disease_sequence_text.get("1.0", "end").strip()
            self._require_inputs(disease_fasta, header, sequence)
            result = add_snp_record_to_database(header=header, sequence=sequence, disease_fasta=disease_fasta)
            merge_result = result["merge_result"]
            self._write_output(
                f"Disease DB updated from entered record: {result['record_header']}\n"
                f"Input records: {merge_result['input_count']}\n"
                f"Output records: {merge_result['output_count']}\n"
                f"Duplicates removed: {len(merge_result['duplicates_removed'])}\n"
            )
            self._set_status("Disease database update complete")
        except Exception as exc:
            self._set_status("Disease database update failed")
            messagebox.showerror("Disease Database Error", str(exc))

    def show_results(self) -> None:
        try:
            results_file = self.results_var.get().strip()
            if not results_file:
                raise ValueError("Results file is required.")

            rows = parse_blast_tabular(results_file)
            if not rows:
                self._write_output(f"Parsed results from {results_file}\nNo BLAST rows found.\n")
                return

            lines = [f"Parsed results from {results_file}"]
            for row in rows:
                lines.append(
                    f"Query: {row['qseqid']} | Match: {row['sseqid']} | Identity: {row['pident']}% | "
                    f"Mismatches: {row['mismatch']} | Query range: {row['qstart']}-{row['qend']} | "
                    f"Reference range: {row['sstart']}-{row['send']}"
                )
            self._write_output("\n".join(lines) + "\n")
        except Exception as exc:
            messagebox.showerror("Parse Error", str(exc))

    def show_snp_analysis(self) -> None:
        try:
            results_file = self.results_var.get().strip()
            blast_bin = self.blast_bin_var.get().strip()
            db_name = self.db_name_var.get().strip()
            query_file = self.query_var.get().strip()
            query_sequence = self.query_sequence_text.get("1.0", "end").strip()
            query_header = self.query_header_var.get().strip() or "user_query"

            if not results_file:
                raise ValueError("Results file is required for SNP analysis.")
            if not blast_bin:
                raise ValueError("BLAST bin folder is required for SNP analysis.")
            if not db_name:
                raise ValueError("BLAST database name or prefix is required for SNP analysis.")
            resolved_db = resolve_database_prefix(db_name, blast_bin)
            self._write_output(f"Using database for SNP analysis: {resolved_db}\n")

            blast_rows = parse_blast_tabular(results_file)
            if not blast_rows:
                raise ValueError("No BLAST rows found in the selected results file.")

            if query_sequence:
                query_source = query_sequence
                selected_query_header = query_header
            elif query_file:
                query_source = query_file
                selected_query_header = None
            else:
                raise ValueError("Provide either a query FASTA file or paste a query sequence.")

            try:
                result = analyze_with_disease_fasta(
                    blast_rows=blast_rows,
                    db_name=db_name,
                    blast_bin=blast_bin,
                    query_source=query_source,
                    disease_fasta=DEFAULT_DISEASE_FASTA,
                    query_header=selected_query_header,
                )
            except ValueError as exc:
                popup_text = (
                    f"SNP analysis could not run for {results_file}\n\n"
                    "The analysis uses the BLAST database and the BLAST result. "
                    "This usually fails when the database prefix, BLAST bin folder, or query input does not match the BLAST run.\n\n"
                    "What to check:\n"
                    "1. The BLAST bin folder contains blastdbcmd.exe.\n"
                    "2. The database prefix is the same one used for Run BLAST.\n"
                    "3. The results file came from that same database.\n"
                    "4. The query input matches the BLAST run.\n\n"
                    f"Details: {exc}"
                )
                self._show_text_popup("SNP Analysis", popup_text)
                self._write_output(f"SNP analysis could not run for {results_file}: {exc}\n")
                return
            popup_text = self._format_snp_analysis(result, results_file)
            self._show_text_popup("SNP Analysis", popup_text)
            self._write_output(f"SNP analysis opened for {results_file}\n")
        except Exception as exc:
            messagebox.showerror("SNP Analysis Error", str(exc))

    def _require_inputs(self, *values: str) -> None:
        if any(not value for value in values):
            raise ValueError("Please fill in all required fields.")

    def update_mode(self) -> None:
        self._set_status("Ready - using BLAST database")

    def _write_output(self, text: str) -> None:
        self.output_text.insert("end", text)
        self.output_text.see("end")

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)
        self.root.update_idletasks()

    def _show_text_popup(self, title: str, text: str) -> None:
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("900x600")

        frame = ttk.Frame(popup, padding=12)
        frame.pack(fill="both", expand=True)

        text_widget = tk.Text(frame, wrap="word")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        text_widget.insert("1.0", text)
        text_widget.configure(state="disabled")

    def _format_snp_analysis(self, result: dict, results_file: str) -> str:
        lines = [
            f"SNP analysis from {results_file}",
            f"Query: {result['query_header']}",
            f"Best match: {result['reference_header']}",
            f"Summary: {result['message']}",
            f"Detected SNP count: {result['snp_count']}",
            "",
        ]

        report_rows = result.get("report_rows", [])
        if not report_rows:
            lines.append("No SNP report rows were generated.")
            return "\n".join(lines)

        for row in report_rows:
            lines.append(
                f"SNP {row['index']}: query pos {row['query_global_position']}, ref pos {row['reference_global_position']}, "
                f"base {row['supposed_base']}->{row['query_base']}, disease={row['disease']}, "
                f"variant={row['variant_name']}, pathogenicity={row['pathogenicity']}, harm={row['harm_level']}"
            )
            lines.append(f"Query context: {row['query_context']}")
            lines.append(f"Reference context: {row['reference_context']}")
            lines.append("")

        return "\n".join(lines)


if __name__ == "__main__":
    root = tk.Tk()
    app = BlastApp(root)
    root.mainloop()
