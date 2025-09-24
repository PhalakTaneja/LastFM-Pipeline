import requests
import pandas as pd
import mysql.connector
import tkinter as tk
from tkinter import messagebox
import customtkinter
from datetime import datetime
import time

customtkinter.set_appearance_mode("dark")

API_KEY = '5833db7d4729b581408f7077396aad98'
MYSQL_USER = 'root'
MYSQL_PASSWORD = '12345678'
MYSQL_DB = 'lastfm_data'



def fetch_and_store_tracks(username):
    try:
        
        url = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={username}&api_key={API_KEY}&format=json&limit=100'
        response = requests.get(url)
        data = response.json()

        if 'error' in data:
            messagebox.showerror("Last.fm Error", f"Error: {data['message']}")
            return

        tracks = data.get('recenttracks', {}).get('track', [])

        if not tracks:
            messagebox.showinfo("No Tracks", "No recent tracks found. User may have scrobbling disabled or set profile to private.")
            return

        
        track_data = []
        for track in tracks:
            ts = track.get('date', {}).get('uts')
            if not ts:
                continue
            
            try:
                timestamp = int(ts)
            except (ValueError, TypeError):
                continue
            played_at_dt = datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')
            
            track_data.append({
                'name': track['name'],
                'artist': track['artist']['#text'],
                'album': track['album']['#text'],
                'played_at': played_at_dt
            })

        df = pd.DataFrame(track_data)

        
        conn = mysql.connector.connect(
            host='localhost',
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        cursor = conn.cursor()

        table_name = f"tracks_{username.replace('-', '_').replace(' ', '_')}"

        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_name}` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            artist VARCHAR(255),
            album VARCHAR(255),
            played_at DATETIME
        );
        """
        cursor.execute(create_table_sql)

        # 5. Clear old data and insert new
        cursor.execute(f"DELETE FROM `{table_name}`")
        cursor.execute(f"ALTER TABLE `{table_name}` AUTO_INCREMENT = 1")

        for _, row in df.iterrows():
            cursor.execute(
                f"""
                INSERT INTO `{table_name}` (name, artist, album, played_at)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    row['name'],
                    row['artist'],
                    row['album'],
                    row['played_at']
                )
            )

        conn.commit()
        cursor.close()
        conn.close()

        messagebox.showinfo("Success", f"Data for '{username}' stored in table '{table_name}'.")

    except Exception as e:
        messagebox.showerror("Error", f"Something went wrong:\n{e}")


# GUI Part
def run_gui():
    #root = tk.Tk()
    root = customtkinter.CTk()
    root.title("Last.fm Track Importer")
    root.geometry("400x150")
    root.resizable(False, False)

    
    #tk.Label(root, text="Enter Last.fm username:", font=("Arial", 12)).pack(pady=15)
    label = customtkinter.CTkLabel(root, text="Enter Last.fm username:", fg_color="transparent",font=("Arial", 12))
    label.pack(pady=15)
    username_entry = tk.Entry(root, font=("Arial", 12), width=30)
    username_entry.pack()

    
    def on_submit():
        username = username_entry.get().strip()
        if username:
            fetch_and_store_tracks(username)
            username_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Input Error", "Please enter a Last.fm username.")

    
    #tk.Button(root, text="Fetch & Save Tracks", command=on_submit, font=("Arial", 11)).pack(pady=15)
    button = customtkinter.CTkButton(root, text="Fetch & Save Tracks", command=on_submit, font=("Arial", 11))
    button.pack(pady=15)


    root.mainloop()



if __name__ == '__main__':
    run_gui()
