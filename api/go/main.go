package main

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

type Status struct {
	Day            string  `json:"day"`
	Trades         int     `json:"trades"`
	RealizedPnLUSD float64 `json:"realized_pnl_usd"`
	Halted         bool    `json:"halted"`
	ServerTimeUTC  string  `json:"server_time_utc"`
}

type Fill struct {
	ID       int64   `json:"id"`
	TS       string  `json:"ts"`
	Mode     string  `json:"mode"`
	Strategy string  `json:"strategy"`
	Symbol   string  `json:"symbol"`
	Side     string  `json:"side"`
	Qty      float64 `json:"qty"`
	Price    float64 `json:"price"`
	Fee      float64 `json:"fee"`
	PnL      float64 `json:"pnl"`
	Note     string  `json:"note"`
}

func main() {
	dbPath := getenv("DB_PATH", "/data/rqe.sqlite")
	port := getenv("API_PORT", "8080")

	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	mux.HandleFunc("/status", func(w http.ResponseWriter, r *http.Request) {
		// daily table keyed by day (UTC)
		day := time.Now().UTC().Format("2006-01-02")

		row := db.QueryRow(`SELECT day, trades, realized_pnl_usd, halted FROM daily WHERE day = ?`, day)

		var s Status
		var haltedInt int
		err := row.Scan(&s.Day, &s.Trades, &s.RealizedPnLUSD, &haltedInt)
		if err != nil {
			// If day not present yet, return a safe default.
			s = Status{Day: day, Trades: 0, RealizedPnLUSD: 0.0, Halted: false}
		} else {
			s.Halted = (haltedInt != 0)
		}
		s.ServerTimeUTC = time.Now().UTC().Format(time.RFC3339)

		writeJSON(w, s)
	})

	mux.HandleFunc("/fills", func(w http.ResponseWriter, r *http.Request) {
		limit := 50
		rows, err := db.Query(`
			SELECT id, ts, mode, strategy, symbol, side, qty, price, fee, pnl, note
			FROM fills
			ORDER BY id DESC
			LIMIT ?`, limit)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer rows.Close()

		out := []Fill{}
		for rows.Next() {
			var f Fill
			if err := rows.Scan(&f.ID, &f.TS, &f.Mode, &f.Strategy, &f.Symbol, &f.Side, &f.Qty, &f.Price, &f.Fee, &f.PnL, &f.Note); err != nil {
				http.Error(w, err.Error(), 500)
				return
			}
			out = append(out, f)
		}
		writeJSON(w, out)
	})

	// “Halt” and “Resume” are safe because they only flip the daily.halted flag.
	mux.HandleFunc("/halt", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "POST required", 405)
			return
		}
		day := time.Now().UTC().Format("2006-01-02")
		_, _ = db.Exec(`INSERT OR IGNORE INTO daily(day,trades,realized_pnl_usd,halted) VALUES(?,?,?,?)`, day, 0, 0.0, 0)
		_, err := db.Exec(`UPDATE daily SET halted=1 WHERE day=?`, day)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		writeJSON(w, map[string]any{"ok": true})
	})

	mux.HandleFunc("/resume", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "POST required", 405)
			return
		}
		day := time.Now().UTC().Format("2006-01-02")
		_, _ = db.Exec(`INSERT OR IGNORE INTO daily(day,trades,realized_pnl_usd,halted) VALUES(?,?,?,?)`, day, 0, 0.0, 0)
		_, err := db.Exec(`UPDATE daily SET halted=0 WHERE day=?`, day)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		writeJSON(w, map[string]any{"ok": true})
	})

	addr := ":" + port
	log.Printf("Go API listening on %s (db=%s)\n", addr, dbPath)
	log.Fatal(http.ListenAndServe(addr, withCORS(mux)))
}

func getenv(k, d string) string {
	v := os.Getenv(k)
	if v == "" {
		return d
	}
	return v
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(v)
}

func withCORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Adjust origins later. For now, permissive for dev.
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if r.Method == http.MethodOptions {
			w.WriteHeader(204)
			return
		}
		next.ServeHTTP(w, r)
	})
}
