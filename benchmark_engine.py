"""
benchmark_engine.py
===================
Three classes that power the benchmarking pipeline:

  DatasetGenerator  – produces reproducible, duplicate-free integer datasets.
  BenchmarkRunner   – times insert / search / delete with warm-up & averaging.
  AnalysisGenerator – derives textual insights from a results DataFrame.

All timings use ``time.perf_counter_ns()`` (nanosecond resolution) and are
returned / stored in **milliseconds** (ms) for human-readable display.

Author  : Generated for UAS Struktur Data
Python  : 3.10+
"""

from __future__ import annotations

import sys
sys.setrecursionlimit(50000)  # Untuk BST/AVL dengan dataset besar

import copy
import random
import time
from typing import Any

import pandas as pd

# ── local imports ────────────────────────────────────────────────────────────
# We import lazily inside methods where needed to avoid circular imports when
# other modules only import this file.  The type hint string literals below
# keep mypy/pyright happy without triggering import-time resolution.


# ── internal utility ─────────────────────────────────────────────────────────

def _fresh_ds(ds_instance: Any) -> Any:
    """
    Return a **new, empty** instance of the same class as *ds_instance*.

    This is the safe alternative to ``copy.deepcopy`` for tree structures:
    deepcopy on a populated BST with 10 000 sorted elements recurses ~10 000
    frames deep and crashes with RecursionError.  Since every benchmark
    always starts from an empty structure anyway, we simply instantiate a
    new object rather than copying the existing (empty) one.

    Parameters
    ----------
    ds_instance : Any
        An instance of any data-structure class.

    Returns
    -------
    Any
        A freshly constructed, empty instance of ``type(ds_instance)``.
    """
    return type(ds_instance)()

# ══════════════════════════════════════════════════════════════════════════════
#  1.  DATASET GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class DatasetGenerator:
    """
    Generates reproducible, **duplicate-free** integer datasets.

    All values are drawn from the range ``[1, size * 10]`` so the value
    space is large enough to keep collisions rare even for the hash table.

    Parameters
    ----------
    seed : int
        Master random seed for full reproducibility across runs.
        Default ``42``.
    """

    # Human-readable type labels used throughout the UI
    TYPES: tuple[str, ...] = ("random", "sorted", "descending")

    def __init__(self, seed: int = 42) -> None:
        self._seed = seed

    # ── public API ───────────────────────────────────────────────────────────

    def generate(self, size: int, data_type: str) -> list[int]:
        """
        Return a list of *size* unique integers shaped by *data_type*.

        Parameters
        ----------
        size : int
            Number of elements to generate.
        data_type : str
            One of ``"random"``, ``"sorted"``, or ``"descending"``.
            The comparison is case-insensitive.

        Returns
        -------
        list[int]
            Duplicate-free integer list of length *size*.

        Raises
        ------
        ValueError
            If *data_type* is not one of the supported values.
        """
        dt = data_type.strip().lower()
        if dt not in self.TYPES:
            raise ValueError(
                f"data_type harus salah satu dari {self.TYPES!r}, diterima {data_type!r}"
            )

        rng = random.Random(self._seed)

        # Build a pool that is large enough for sampling without replacement.
        pool_size = max(size * 10, size + 1_000)
        population = list(range(1, pool_size + 1))
        values: list[int] = rng.sample(population, size)

        if dt == "sorted":
            values.sort()
        elif dt == "descending":
            values.sort(reverse=True)
        # "random" → leave as-is (already shuffled by sample())

        return values

    def generate_search_targets(
        self,
        dataset: list[int],
        n: int = 100,
        seed_offset: int = 1,
    ) -> list[int]:
        """
        Pick *n* elements that are **guaranteed to exist** in *dataset*.

        Used for search and delete benchmarks so we always hit real entries.

        Parameters
        ----------
        dataset : list[int]
            The already-generated dataset.
        n : int
            How many targets to pick (default 100).
        seed_offset : int
            Added to the master seed so search targets differ from insert order.

        Returns
        -------
        list[int]
            A list of *n* values drawn from *dataset*.
        """
        n       = min(n, len(dataset))
        rng     = random.Random(self._seed + seed_offset)
        return rng.sample(dataset, n)


# ══════════════════════════════════════════════════════════════════════════════
#  2.  BENCHMARK RUNNER
# ══════════════════════════════════════════════════════════════════════════════

class BenchmarkRunner:
    """
    Times data-structure operations with nanosecond precision.

    Design choices
    --------------
    * **Warm-up pass** – one un-timed dry run so Python's function-call
      cache, branch predictor, and any JIT effects are primed before the
      clock starts.
    * **Averaging** – search and delete are repeated ``n_repeats`` times
      (default 5) on fresh structure copies; the mean is returned to
      smooth out OS scheduling spikes.
    * ``time.perf_counter_ns()`` is used for all timing; results are
      converted to **milliseconds** before being returned.

    Parameters
    ----------
    n_repeats : int
        Number of timed repetitions for search and delete (default 5).
    search_sample_size : int
        Number of elements to search / delete per repetition (default 100).
    """

    NS_TO_MS: float = 1e-6   # nanoseconds → milliseconds

    def __init__(
        self,
        n_repeats:          int = 5,
        search_sample_size: int = 100,
    ) -> None:
        self._n_repeats          = n_repeats
        self._search_sample_size = search_sample_size
        self._generator          = DatasetGenerator()

    # ── public API ───────────────────────────────────────────────────────────

    def run_benchmark(
        self,
        ds_instance: Any,
        dataset:     list[int],
        operation:   str,
    ) -> float:
        """
        Benchmark a single *operation* on *ds_instance* using *dataset*.

        Parameters
        ----------
        ds_instance : Any
            A fresh (empty) instance of one of the data-structure classes
            from ``data_structures.py``.
        dataset : list[int]
            The pre-generated list of integers for this run.
        operation : str
            One of ``"insert"``, ``"search"``, or ``"delete"``
            (case-insensitive).

        Returns
        -------
        float
            Elapsed time in **milliseconds**.
            For search / delete this is the *average* over ``n_repeats``
            independent timed runs.

        Raises
        ------
        ValueError
            If *operation* is not one of the three supported strings.
        """
        op = operation.strip().lower()
        if op == "insert":
            return self._bench_insert(ds_instance, dataset)
        if op == "search":
            return self._bench_search(ds_instance, dataset)
        if op == "delete":
            return self._bench_delete(ds_instance, dataset)
        raise ValueError(
            f"operasi harus 'insert', 'search', atau 'delete', diterima {operation!r}"
        )

    def run_full_suite(
        self,
        ds_class:   type,
        ds_name:    str,
        sizes:      list[int]  | None = None,
        data_types: list[str]  | None = None,
    ) -> pd.DataFrame:
        """
        Run insert, search, and delete benchmarks for every combination of
        *size* × *data_type* and return results as a tidy DataFrame.

        Parameters
        ----------
        ds_class : type
            The uninitialised class (e.g. ``ArrayDS``).
        ds_name : str
            Human-readable label (e.g. ``"Array"``).
        sizes : list[int] | None
            Dataset sizes to test.  Defaults to ``[100, 1_000, 10_000]``.
        data_types : list[str] | None
            Dataset types to test.  Defaults to all three.

        Returns
        -------
        pd.DataFrame
            Columns: ``structure``, ``size``, ``data_type``,
                      ``insert_ms``, ``search_ms``, ``delete_ms``.
        """
        if sizes      is None: sizes      = [100, 1_000, 10_000]
        if data_types is None: data_types = list(DatasetGenerator.TYPES)

        rows: list[dict] = []
        gen  = DatasetGenerator()

        for size in sizes:
            for dt in data_types:
                dataset = gen.generate(size, dt)

                insert_ms = self.run_benchmark(ds_class(), dataset, "insert")
                search_ms = self.run_benchmark(ds_class(), dataset, "search")
                delete_ms = self.run_benchmark(ds_class(), dataset, "delete")

                rows.append({
                    "structure": ds_name,
                    "size":       size,
                    "data_type":  dt,
                    "insert_ms":  insert_ms,
                    "search_ms":  search_ms,
                    "delete_ms":  delete_ms,
                })

        return pd.DataFrame(rows)

    # ── private: per-operation timers ────────────────────────────────────────

    def _bench_insert(self, ds_instance: Any, dataset: list[int]) -> float:
        """
        Measure the total time to insert **all** elements of *dataset*.

        A warm-up run inserts the first element and immediately discards
        the instance so the real timer starts on a clean structure.

        Returns
        -------
        float
            Total insert time in ms (single run – no averaging needed
            because we are inserting the full dataset each time).
        """
        # ── warm-up (not timed) ──────────────────────────────────────────────
        # Build a throw-away empty instance and insert just the first element.
        # Using _fresh_ds() instead of copy.deepcopy() avoids RecursionError
        # on deep BST / AVL trees at large dataset sizes.
        warm_ds = _fresh_ds(ds_instance)
        if dataset:
            warm_ds.insert(dataset[0])
        del warm_ds

        # ── timed run ────────────────────────────────────────────────────────
        fresh_ds = _fresh_ds(ds_instance)
        t_start  = time.perf_counter_ns()
        for value in dataset:
            fresh_ds.insert(value)
        t_end    = time.perf_counter_ns()

        return (t_end - t_start) * self.NS_TO_MS

    def _bench_search(self, ds_instance: Any, dataset: list[int]) -> float:
        """
        Measure the **average** time to search for
        ``search_sample_size`` random elements that exist in the structure.

        Steps
        -----
        1. Populate a fresh structure with *dataset*.
        2. Pick ``search_sample_size`` guaranteed-present targets.
        3. Warm-up: search for the first target (un-timed).
        4. Repeat ``n_repeats`` times: time searching all targets.
        5. Return the mean elapsed time in ms.

        Returns
        -------
        float
            Average search time in ms over ``n_repeats`` runs.
        """
        targets = self._generator.generate_search_targets(
            dataset, self._search_sample_size
        )

        # ── build the populated structure (not timed) ────────────────────────
        # _fresh_ds() constructs a clean empty instance — safe at any depth.
        populated = _fresh_ds(ds_instance)
        for value in dataset:
            populated.insert(value)

        # ── warm-up ──────────────────────────────────────────────────────────
        if targets:
            populated.search(targets[0])

        # ── timed repeats ────────────────────────────────────────────────────
        elapsed_ns: list[int] = []
        for _ in range(self._n_repeats):
            t_start = time.perf_counter_ns()
            for t in targets:
                populated.search(t)
            t_end = time.perf_counter_ns()
            elapsed_ns.append(t_end - t_start)

        avg_ns = sum(elapsed_ns) / len(elapsed_ns)
        return avg_ns * self.NS_TO_MS

    def _bench_delete(self, ds_instance: Any, dataset: list[int]) -> float:
        """
        Measure the **average** time to delete ``search_sample_size``
        random elements from a populated structure.

        Design: Restore Technique
        -------------------------
        The previous approach rebuilt the full structure from scratch for
        every repeat.  On a BST fed sorted/descending data the tree
        degenerates to a linked list of height *n*, making each insert
        O(n).  Rebuilding 10 000 elements × n_repeats times gives
        O(n² × repeats) total cost — ~50 seconds for n=10 000.

        The fix: build the structure **once**, then for each repeat:
          1. (timed)   delete all target values.
          2. (un-timed) re-insert those same target values to restore
                        the structure to its pre-delete state.

        Only ``search_sample_size`` (≤100) values are re-inserted per
        repeat instead of the full dataset, so the overhead is negligible
        at any size.  The measured time covers only the delete phase.

        Steps
        -----
        1. Build the populated structure once from *dataset*.
        2. Pick ``search_sample_size`` guaranteed-present targets.
        3. Warm-up: delete then restore the first target (un-timed).
        4. Repeat ``n_repeats`` times:
             a. Time deleting all targets.
             b. (un-timed) re-insert all targets to restore state.
        5. Return the mean elapsed delete time in ms.

        Returns
        -------
        float
            Average delete time in ms over ``n_repeats`` runs.
        """
        targets = self._generator.generate_search_targets(
            dataset, self._search_sample_size, seed_offset=2
        )

        # ── build the structure once (not timed) ─────────────────────────────
        # _fresh_ds() constructs an empty instance — safe at any dataset size.
        working = _fresh_ds(ds_instance)
        for value in dataset:
            working.insert(value)

        # ── warm-up: delete + restore first target (not timed) ───────────────
        if targets:
            working.delete(targets[0])
            working.insert(targets[0])   # restore so state stays consistent

        # ── timed repeats using restore instead of full rebuild ───────────────
        # After each timed delete pass, re-insert the targets so the next
        # repeat starts from the same populated state.  This costs only
        # O(search_sample_size) inserts instead of O(n) inserts per repeat.
        elapsed_ns: list[int] = []
        for _ in range(self._n_repeats):
            t_start = time.perf_counter_ns()
            for t in targets:
                working.delete(t)
            t_end = time.perf_counter_ns()
            elapsed_ns.append(t_end - t_start)
            # Restore deleted values (not timed) so the next repeat is valid
            for t in targets:
                working.insert(t)

        avg_ns = sum(elapsed_ns) / len(elapsed_ns)
        return avg_ns * self.NS_TO_MS


# ══════════════════════════════════════════════════════════════════════════════
#  3.  ANALYSIS GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class AnalysisGenerator:
    """
    Derives automated textual insights from benchmark results.

    ``generate_analysis`` is fully implemented and returns a rich ``dict``
    of human-readable strings that ``app.py`` can render directly.

    Parameters
    ----------
    None
    """

    # Maps structure names to their theoretical complexities
    _COMPLEXITY: dict[str, dict[str, str]] = {
        "Array (Linear)":  {"insert": "O(1)", "search": "O(n)",      "delete": "O(n)"},
        "Array (Binary)":  {"insert": "O(1)", "search": "O(log n)",  "delete": "O(n)"},
        "Hash Table":      {"insert": "O(1)", "search": "O(1)",      "delete": "O(1)"},
        "BST":             {"insert": "O(h)", "search": "O(h)",      "delete": "O(h)"},
        "AVL Tree":        {"insert": "O(log n)", "search": "O(log n)", "delete": "O(log n)"},
    }

    # ── public API ───────────────────────────────────────────────────────────

    def generate_analysis(self, results_df: pd.DataFrame) -> dict:
        """
        Analyse *results_df* and return a dictionary of insight strings.

        The returned dict has the following keys:

        ``"overall_winner_insert"``   : str – fastest structure for insert
        ``"overall_winner_search"``   : str – fastest structure for search
        ``"overall_winner_delete"``   : str – fastest structure for delete
        ``"summary_table"``           : pd.DataFrame – per-structure mean times
        ``"scaling_insights"``        : list[str] – scaling observations
        ``"data_type_insights"``      : list[str] – how data ordering affects perf
        ``"complexity_comparison"``   : dict – theoretical vs observed notes
        ``"recommendation"``          : str – overall recommendation paragraph
        ``"podium"``                  : dict[str, list[str]] – top-3 per operation

        Parameters
        ----------
        results_df : pd.DataFrame
            DataFrame produced by ``BenchmarkRunner.run_full_suite`` or
            assembled in ``app.py``.  Required columns:
            ``structure``, ``size``, ``data_type``,
            ``insert_ms``, ``search_ms``, ``delete_ms``.

        Returns
        -------
        dict
            Insight dictionary described above.
        """
        if results_df is None or results_df.empty:
            return {"error": "Tidak ada data benchmark yang tersedia untuk dianalisis."}

        df = results_df.copy()

        insights: dict = {}

        # ── 1. Overall winners (mean across all sizes & data types) ──────────
        mean_by_struct = (
            df.groupby("structure")[["insert_ms", "search_ms", "delete_ms"]]
            .mean()
            .round(4)
        )
        insights["summary_table"] = mean_by_struct.reset_index()

        def _winner(col: str) -> str:
            idx = mean_by_struct[col].idxmin()
            val = mean_by_struct.loc[idx, col]
            return f"{idx}  ({val:.4f} ms rata-rata)"

        insights["overall_winner_insert"] = _winner("insert_ms")
        insights["overall_winner_search"] = _winner("search_ms")
        insights["overall_winner_delete"] = _winner("delete_ms")

        # ── 2. Podium (top-3) per operation ──────────────────────────────────
        podium: dict[str, list[str]] = {}
        for op, col in [("insert", "insert_ms"), ("search", "search_ms"), ("delete", "delete_ms")]:
            ranked = mean_by_struct[col].sort_values()
            podium[op] = [
                f"{i+1}. {name}  ({val:.4f} ms)"
                for i, (name, val) in enumerate(ranked.items())
            ]
        insights["podium"] = podium

        # ── 3. Scaling insights ───────────────────────────────────────────────
        sizes = sorted(df["size"].unique())
        scaling_notes: list[str] = []

        if len(sizes) >= 2:
            smallest, largest = sizes[0], sizes[-1]
            scale_factor = largest / smallest

            for struct in df["structure"].unique():
                sub = df[df["structure"] == struct]

                for op, col in [
                    ("insert", "insert_ms"),
                    ("search", "search_ms"),
                    ("delete", "delete_ms"),
                ]:
                    t_small = sub[sub["size"] == smallest][col].mean()
                    t_large = sub[sub["size"] == largest][col].mean()

                    if t_small > 0:
                        observed_ratio = t_large / t_small
                        if observed_ratio < scale_factor * 0.15:
                            growth = "sub-linear (mendekati O(1))"
                        elif observed_ratio < scale_factor * 0.6:
                            growth = "logaritmik (O(log n))"
                        elif observed_ratio < scale_factor * 1.5:
                            growth = "linear (O(n))"
                        elif observed_ratio < scale_factor ** 1.5:
                            growth = "super-linear (O(n log n))"
                        else:
                            growth = "kuadratik atau lebih buruk (O(n²+))"

                        scaling_notes.append(
                            f"{struct} – {op}: berskala {growth} "
                            f"(×{observed_ratio:.1f} waktu untuk ×{scale_factor:.0f} data)"
                        )

        insights["scaling_insights"] = scaling_notes

        # ── 4. Data-type insights ─────────────────────────────────────────────
        dtype_notes: list[str] = []
        data_types_present = df["data_type"].unique()

        if len(data_types_present) >= 2:
            for struct in df["structure"].unique():
                sub = df[df["structure"] == struct]
                for op, col in [
                    ("insert", "insert_ms"),
                    ("search", "search_ms"),
                    ("delete", "delete_ms"),
                ]:
                    dt_means = (
                        sub.groupby("data_type")[col].mean().round(4)
                    )
                    if len(dt_means) < 2:
                        continue
                    best_dt  = dt_means.idxmin()
                    worst_dt = dt_means.idxmax()
                    spread   = dt_means.max() - dt_means.min()

                    if spread > 0.001:   # only report meaningful differences
                        dtype_notes.append(
                            f"{struct} – {op}: tercepat pada data '{best_dt}', "
                            f"terlambat pada data '{worst_dt}' "
                            f"(selisih {spread:.4f} ms)"
                        )

        insights["data_type_insights"] = dtype_notes if dtype_notes else [
            "Tidak ada perbedaan performa signifikan yang terdeteksi antar tipe data."
        ]

        # ── 5. Theoretical vs observed complexity notes ───────────────────────
        complexity_notes: dict[str, str] = {}
        for struct, complexities in self._COMPLEXITY.items():
            matching = df[df["structure"].str.contains(
                struct.split()[0], case=False, regex=False
            )]
            if matching.empty:
                continue
            notes_parts: list[str] = []
            for op, col in [
                ("insert", "insert_ms"),
                ("search", "search_ms"),
                ("delete", "delete_ms"),
            ]:
                theory = complexities.get(op, "N/A")
                avg_ms = matching[col].mean()
                notes_parts.append(f"{op}: {theory} → {avg_ms:.4f} ms rata-rata")
            complexity_notes[struct] = " | ".join(notes_parts)

        insights["complexity_comparison"] = complexity_notes

        # ── 6. Overall recommendation paragraph ──────────────────────────────
        best_search  = mean_by_struct["search_ms"].idxmin()
        best_insert  = mean_by_struct["insert_ms"].idxmin()
        best_delete  = mean_by_struct["delete_ms"].idxmin()
        best_overall = (
            mean_by_struct[["insert_ms", "search_ms", "delete_ms"]]
            .mean(axis=1)
            .idxmin()
        )

        insights["recommendation"] = (
            f"Berdasarkan hasil benchmark, **{best_overall}** memberikan performa "
            f"terbaik secara keseluruhan untuk operasi insert, pencarian, dan hapus. "
            f"Untuk beban kerja pencarian intensif, gunakan **{best_search}**. "
            f"Untuk beban kerja insert intensif, gunakan **{best_insert}**. "
            f"Untuk beban kerja hapus intensif, gunakan **{best_delete}**. "
            f"Hash Table unggul pada operasi rata-rata O(1) tetapi menurun "
            f"saat faktor beban tinggi. AVL Tree menjamin O(log n) kasus terburuk "
            f"dan ideal ketika data masuk dalam urutan terurut (yang mendegradasi BST "
            f"menjadi O(n)). Array paling sederhana namun buruk untuk pencarian dan hapus."
        )

        return insights


# ══════════════════════════════════════════════════════════════════════════════
#  Quick self-test  (python benchmark_engine.py)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")   # ensure data_structures.py is on path

    from data_structures import (
        ArrayDS,
        HashTableDS,
        BinarySearchTreeDS,
        AVLTreeDS,
    )

    gen = DatasetGenerator()

    # ── DatasetGenerator ────────────────────────────────────────────────────
    for dt in DatasetGenerator.TYPES:
        d = gen.generate(200, dt)
        assert len(d) == 200,      f"{dt}: wrong length"
        assert len(set(d)) == 200, f"{dt}: duplicates found"
    r   = gen.generate(200, "random")
    s   = gen.generate(200, "sorted")
    desc = gen.generate(200, "descending")
    assert s == sorted(s),             "sorted dataset not sorted"
    assert desc == sorted(desc, reverse=True), "descending dataset not descending"
    print("DatasetGenerator  ✓")

    # ── BenchmarkRunner ──────────────────────────────────────────────────────
    runner  = BenchmarkRunner(n_repeats=3, search_sample_size=20)
    dataset = gen.generate(500, "random")

    for DS, name in [
        (ArrayDS,             "Array"),
        (HashTableDS,         "HashTable"),
        (BinarySearchTreeDS,  "BST"),
        (AVLTreeDS,           "AVL"),
    ]:
        for op in ("insert", "search", "delete"):
            ms = runner.run_benchmark(DS(), dataset, op)
            assert ms >= 0, f"{name} {op}: negative time"
        print(f"  BenchmarkRunner [{name:10s}]  ✓")

    # ── run_full_suite ───────────────────────────────────────────────────────
    runner2 = BenchmarkRunner(n_repeats=2, search_sample_size=10)
    df = runner2.run_full_suite(
        AVLTreeDS, "AVL Tree",
        sizes=[100, 500],
        data_types=["random", "sorted"],
    )
    assert set(df.columns) >= {"structure", "size", "data_type",
                                "insert_ms", "search_ms", "delete_ms"}
    assert len(df) == 4    # 2 sizes × 2 data_types
    print("  run_full_suite              ✓")

    # ── AnalysisGenerator ────────────────────────────────────────────────────
    # Build a small combined DataFrame for analysis
    frames = []
    small_runner = BenchmarkRunner(n_repeats=2, search_sample_size=10)
    for DS, label in [
        (ArrayDS,            "Array"),
        (HashTableDS,        "Hash Table"),
        (BinarySearchTreeDS, "BST"),
        (AVLTreeDS,          "AVL Tree"),
    ]:
        frames.append(
            small_runner.run_full_suite(DS, label, sizes=[100, 500], data_types=["random"])
        )
    combined = pd.concat(frames, ignore_index=True)

    analyser = AnalysisGenerator()
    result   = analyser.generate_analysis(combined)

    required_keys = {
        "overall_winner_insert", "overall_winner_search", "overall_winner_delete",
        "summary_table", "scaling_insights", "data_type_insights",
        "complexity_comparison", "recommendation", "podium",
    }
    missing = required_keys - result.keys()
    assert not missing, f"Missing keys in analysis: {missing}"
    assert isinstance(result["summary_table"], pd.DataFrame)
    assert isinstance(result["scaling_insights"], list)
    assert isinstance(result["recommendation"], str)
    print("AnalysisGenerator           ✓")

    print("\nAll benchmark_engine tests passed ✓")
