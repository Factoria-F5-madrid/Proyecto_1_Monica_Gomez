import tkinter as tk
from tkinter import messagebox, ttk
import time
import sqlite3
from datetime import datetime

class TaximeterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("F5 Taximeter")

        # Estado del taxímetro
        self.trip_active = False
        self.state = None          # 'stopped', 'moving' o None
        self.state_start_time = None
        self.stopped_time = 0
        self.moving_time = 0
        self.timer_id = None

        # Conectar a base de datos SQLite
        self.conn = sqlite3.connect("taximeter.db")
        self.create_table()

        # Widgets
        self.label_status = tk.Label(root, text="Press Start", font=("Arial", 16))
        self.label_status.pack(pady=10)

        self.label_stopped = tk.Label(root, text="Stopped time: 0.0s", font=("Arial", 12))
        self.label_stopped.pack()

        self.label_moving = tk.Label(root, text="Moving time: 0.0s", font=("Arial", 12))
        self.label_moving.pack()

        self.label_fare = tk.Label(root, text="Fare: €0.00", font=("Arial", 14, "bold"))
        self.label_fare.pack(pady=10)

        # Botones
        frame_buttons = tk.Frame(root)
        frame_buttons.pack(pady=10)

        btn_start = tk.Button(frame_buttons, text="Start", width=10, command=self.start_trip)
        btn_start.grid(row=0, column=0, padx=5)

        btn_stop = tk.Button(frame_buttons, text="Stop", width=10, command=self.stop_trip)
        btn_stop.grid(row=0, column=1, padx=5)

        btn_move = tk.Button(frame_buttons, text="Move", width=10, command=self.move_trip)
        btn_move.grid(row=0, column=2, padx=5)

        btn_finish = tk.Button(frame_buttons, text="Finish", width=10, command=self.finish_trip)
        btn_finish.grid(row=0, column=3, padx=5)

        btn_view = tk.Button(frame_buttons, text="View Trips", width=10, command=self.view_trips)
        btn_view.grid(row=0, column=4, padx=5)

    def create_table(self):
        """Crear la tabla si no existe."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT,
                stopped_time REAL,
                moving_time REAL,
                total_fare REAL
            )
        """)
        self.conn.commit()

    def save_trip(self, stopped_time, moving_time, total_fare):
        """Guardar un viaje en la base de datos."""
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO trips (datetime, stopped_time, moving_time, total_fare)
            VALUES (?, ?, ?, ?)
        """, (now, stopped_time, moving_time, total_fare))
        self.conn.commit()

    def view_trips(self):
        """Mostrar historial de viajes en una ventana."""
        win = tk.Toplevel(self.root)
        win.title("Trip History")

        tree = ttk.Treeview(win, columns=("Date", "Stopped Time", "Moving Time", "Fare"), show="headings")
        tree.heading("Date", text="Date & Time")
        tree.heading("Stopped Time", text="Stopped Time (s)")
        tree.heading("Moving Time", text="Moving Time (s)")
        tree.heading("Fare", text="Fare (€)")
        tree.pack(fill=tk.BOTH, expand=True)

        # Consultar datos
        cursor = self.conn.cursor()
        cursor.execute("SELECT datetime, stopped_time, moving_time, total_fare FROM trips ORDER BY id DESC")
        rows = cursor.fetchall()

        for row in rows:
            tree.insert("", tk.END, values=row)

    def start_trip(self):
        if self.trip_active:
            messagebox.showerror("Error", "A trip is already in progress.")
            return

        self.trip_active = True
        self.state = 'stopped'
        self.state_start_time = time.time()
        self.stopped_time = 0
        self.moving_time = 0
        self.root.configure(bg="red")  # Color inicial (stopped)
        self.update_labels()

        # Lanzar temporizador
        self.timer_id = self.root.after(500, self.update_timer)

    def stop_trip(self):
        if not self.trip_active:
            messagebox.showerror("Error", "No active trip. Please start first.")
            return

        self.update_time_accumulated()
        self.state = 'stopped'
        self.state_start_time = time.time()
        self.root.configure(bg="red")
        self.update_labels()

    def move_trip(self):
        if not self.trip_active:
            messagebox.showerror("Error", "No active trip. Please start first.")
            return

        self.update_time_accumulated()
        self.state = 'moving'
        self.state_start_time = time.time()
        self.root.configure(bg="green")
        self.update_labels()

    def finish_trip(self):
        if not self.trip_active:
            messagebox.showerror("Error", "No active trip to finish.")
            return

        # Sumar tiempo pendiente
        self.update_time_accumulated()

        total_fare = self.calculate_fare(self.stopped_time, self.moving_time)

        # Guardar en la base de datos
        self.save_trip(self.stopped_time, self.moving_time, total_fare)

        summary = (
            f"--- Trip Summary ---\n"
            f"Stopped time: {self.stopped_time:.1f} seconds\n"
            f"Moving time: {self.moving_time:.1f} seconds\n"
            f"Total fare: €{total_fare:.2f}\n"
            f"---------------------"
        )

        messagebox.showinfo("Trip Summary", summary)

        print("\n--- PRINTING TICKET ---")
        print(summary)
        print("------------------------\n")

        # Parar viaje y el temporizador
        self.trip_active = False
        self.state = None
        self.state_start_time = None
        self.root.configure(bg="white")

        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        self.update_labels()

    def update_time_accumulated(self):
        if not self.trip_active or self.state_start_time is None:
            return

        now = time.time()
        duration = now - self.state_start_time

        if self.state == 'moving':
            self.moving_time += duration
        elif self.state == 'stopped':
            self.stopped_time += duration

        self.state_start_time = now

    def calculate_fare(self, seconds_stopped, seconds_moving):
        return seconds_stopped * 0.02 + seconds_moving * 0.05

    def update_labels(self):
        self.label_status.config(
            text=f"Status: {self.state if self.state else 'Idle'}"
        )
        self.label_stopped.config(
            text=f"Stopped time: {self.stopped_time:.1f} s"
        )
        self.label_moving.config(
            text=f"Moving time: {self.moving_time:.1f} s"
        )
        total_fare = self.calculate_fare(self.stopped_time, self.moving_time)
        self.label_fare.config(
            text=f"Fare: €{total_fare:.2f}"
        )

    def update_timer(self):
        if self.trip_active and self.state and self.state_start_time is not None:
            now = time.time()
            elapsed = now - self.state_start_time

            if self.state == 'moving':
                total_moving = self.moving_time + elapsed
                self.label_moving.config(
                    text=f"Moving time: {total_moving:.1f} s"
                )
            elif self.state == 'stopped':
                total_stopped = self.stopped_time + elapsed
                self.label_stopped.config(
                    text=f"Stopped time: {total_stopped:.1f} s"
                )

            total_fare = self.calculate_fare(
                self.stopped_time + (elapsed if self.state == 'stopped' else 0),
                self.moving_time + (elapsed if self.state == 'moving' else 0)
            )
            self.label_fare.config(
                text=f"Fare: €{total_fare:.2f}"
            )

        if self.trip_active:
            self.timer_id = self.root.after(500, self.update_timer)

if __name__ == "__main__":
    root = tk.Tk()
    app = TaximeterGUI(root)
    root.mainloop()
