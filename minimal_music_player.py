import customtkinter as ctk
from tkinter import filedialog
import os
import pygame

# ------------------------------------------U I--------------------------------------------- #
#region APP UI - START
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MusicPlayer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        #Audio Engine
        pygame.mixer.init()
        self.current_song_index=-1
        self.is_paused=False
        self.song_duration=0
        self.song_start_time=0
        
        self.music_files=[]
        self.imported_folder=[]
        self.title("Minimal Music Player")
        self.geometry("420x650")
        self.resizable(True, True)

        # Main player container
        self.player = ctk.CTkFrame(
            self,
            corner_radius=24,
            fg_color="#181818"
        )
        self.player.pack(
            padx=5,
            pady=5,
            fill="both",
            expand=True
        )

        # -----------------------------
        # Album artwork placeholder
        # -----------------------------
        self.artwork = ctk.CTkFrame(
            self.player,
            width=300,
            height=270,
            corner_radius=18,
            fg_color="#252525"
        )
        self.artwork.pack(pady=(35, 25))
        self.artwork.pack_propagate(False)

        self.artwork_label = ctk.CTkLabel(
            self.artwork,
            text="♪",
            font=ctk.CTkFont(size=80, weight="bold"),
            text_color="#666666"
        )
        self.artwork_label.place(relx=0.5, rely=0.5, anchor="center")

        # Song information
        # -----------------------------
        self.song_title = ctk.CTkLabel(
            self.player,
            text="No song selected",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.song_title.pack(pady=(0, 0))

        self.artist = ctk.CTkLabel(
            self.player,
            text="Unknown Artist",
            font=ctk.CTkFont(size=12),
            text_color="#999999"
        )
        self.artist.pack()

        # Progress bar
        # -----------------------------
        self.progress = ctk.CTkSlider(
            self.player,
            from_=0,
            to=100,
            height=5,
            button_length=12,
            command=self.seek_song
        )
        self.progress.set(0)
        self.progress.pack(
            fill="x",
            padx=35,
            pady=(20, 5)
        )

        self.time_frame = ctk.CTkFrame(
            self.player,
            fg_color="transparent"
        )
        self.time_frame.pack(fill="x", padx=35)

        self.curr_time_label=ctk.CTkLabel(          #FIXME: curr -> current
            self.time_frame,
            text="0:00",
            text_color="#888888"
        )
        
        self.curr_time_label.pack(side="left")

        self.total_time_label=ctk.CTkLabel(
            self.time_frame,
            text="0:00",
            text_color="#888888"
        )
        self.total_time_label.pack(side="right")

        # -----------------------------
        # Playback controls
        # -----------------------------
        self.controls = ctk.CTkFrame(
            self.player,
            fg_color="transparent"
        )
        self.controls.pack(pady=5)

        self.previous_button=ctk.CTkButton(
            self.controls,
            text="↶",
            width=50,
            height=40,
            corner_radius=20,
            fg_color="transparent",
            hover_color="#292929",
            font=ctk.CTkFont(size=22),
            command=self.previous_song
        ).grid(row=0, column=0, padx=5)

        self.play_button = ctk.CTkButton(
            self.controls,
            text="▶",
            width=65,
            height=55,
            corner_radius=28,
            font=ctk.CTkFont(size=24, weight="bold"),
            command=self.toggle_play_pause
        )
        self.play_button.grid(row=0, column=1, padx=5)

        self.next_button=ctk.CTkButton(
            self.controls,
            text="↷",
            width=50,
            height=40,
            corner_radius=20,
            fg_color="transparent",
            hover_color="#292929",
            font=ctk.CTkFont(size=22),
            command=self.next_song
        ).grid(row=0, column=2, padx=5)

        # -----------------------------
        # Import Music Controls
        # -----------------------------
        self.bottom = ctk.CTkFrame(
            self.player,
            fg_color="transparent"
        )
        self.bottom.pack(
            side="bottom",
            fill="x",
            padx=20,
            pady=20
        )
        #Playlist btn
        self.playlist_button=ctk.CTkButton(
            self.bottom,
            text=" ☰  Playlist",
            height=40,
            corner_radius=12,
            font=ctk.CTkFont(size=12,weight="bold"),
            command=self.show_playlist
        )
        self.playlist_button.pack(
            fill="x", pady=(0,8)
        )

        # Main import button
        self.import_button = ctk.CTkButton(
            self.bottom,
            text="+  Import Music",
            height=42,
            width=100,
            corner_radius=12,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.import_music_folder
        )

        self.import_button.pack()

        # Small floating-style import button
        self.small_import_button = ctk.CTkButton(
            self.player,
            text="+",
            width=38,
            height=38,
            corner_radius=19,
            font=ctk.CTkFont(size=22, weight="bold"),
            command=self.import_music_folder
        )
        self.playlist_view=ctk.CTkFrame(
            self,
            width=300,
            corner_radius=24,
            fg_color="#181818"
        )
        
        #Playlist header
        self.playlist_header=ctk.CTkFrame(
            self.playlist_view,
            fg_color="transparent"
        )
        
        self.playlist_header.pack(
            fill="x",
            padx=20,
            pady=(20,10)
        )
        
        self.back_buttom=ctk.CTkButton(
            self.playlist_header,
            text="←",
            width=30,
            height=30,
            corner_radius=20,
            fg_color="transparent",
            hover_color="#292929",
            font=ctk.CTkFont(size=20),
            command=self.hide_playlist
        )
        self.back_buttom.pack(side="left")
        
        self.playlist_title=ctk.CTkLabel(
            self.playlist_header,
            text="Playlist",
            font=ctk.CTkFont(size=20,weight="bold")
        )
        self.playlist_title.pack(
            side="left",
            padx=12
        )
        self.song_count_label=ctk.CTkLabel(
            self.playlist_header,
            text="0 songs",
            text_color="#888888"
        )
        self.song_count_label.pack(side="right")
        
        self.playlist_scroll=ctk.CTkScrollableFrame(
            self.playlist_view,
            corner_radius=12,
            fg_color="transparent"
        )
        self.playlist_scroll.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(5,15)
        )
    #region APP UI - END
    
    def update_time_labels(self, current, total):
        current_minutes = int(current // 60)
        current_seconds = int(current % 60)
        total_minutes = int(total // 60)
        total_seconds = int(total % 60)

        self.curr_time_label.configure(
            text=f"{current_minutes}:{current_seconds:02d}"
        )

        self.total_time_label.configure(
            text=f"{total_minutes}:{total_seconds:02d}"
        )
    
    def update_progress(self):
        if self.current_song_index == -1:
            return

        if self.song_duration <= 0:
            return

        current_time = pygame.mixer.music.get_pos() / 1000

        if current_time < 0:
            return

        progress = (
            current_time / self.song_duration
        ) * 100
        progress = min(
            max(progress, 0),
            100
        )
        self.progress.set(progress)
        self.update_time_labels(
            current_time,
            self.song_duration
        )
        self.after(
            500,
            self.update_progress
        )
    def seek_song(self, value):
        if self.current_song_index == -1:
            return

        if self.song_duration <= 0:
            return

        new_position = (
            float(value) / 100
        ) * self.song_duration

        try:
            pygame.mixer.music.set_pos(
                new_position
            )

        except Exception as error:
            print("Seek error:", error)
        
    def toggle_play_pause(self):
        if self.current_song_index == -1:
            # Nothing playing → play first song
            if self.music_files:
                self.play_song(0)
            return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.play_button.configure(
                text="❚"
            )
        else:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.play_button.configure(
                text="▶"
            )
    def next_song(self):
        if not self.music_files:
            return

        if self.current_song_index == -1:
            self.play_song(0)
            return

        next_index = self.current_song_index + 1
        if next_index >= len(self.music_files):
            next_index = 0

        self.play_song(next_index)

    def previous_song(self):
        if not self.music_files:
            return

        if self.current_song_index == -1:
            self.play_song(0)
            return

        previous_index = self.current_song_index - 1
        if previous_index < 0:
            previous_index = len(self.music_files) - 1

        self.play_song(previous_index)
    
    def check_song_end(self):
        if (
            self.current_song_index != -1
            and not self.is_paused
            and not pygame.mixer.music.get_busy()
        ):
            self.next_song()

        self.after(
            500,
            self.check_song_end
        )
        
    def import_music_folder(self):
            folder = filedialog.askdirectory(
                title="Select Music Folder"
            )
    
            if not folder:
                return
    
            supported_formats = (
                ".mp3",
                ".wav",
                ".flac",
                ".m4a",
                ".ogg"
            )
    
            songs = []
    
            for filename in os.listdir(folder):
    
                file_path = os.path.join(folder, filename)
    
                if (
                    os.path.isfile(file_path)
                    and filename.lower().endswith(supported_formats)
                ):
                    songs.append(file_path)
    
            # Add newly found songs to the library
            for song in songs:
                if song not in self.music_files:
                    self.music_files.append(song)
    
            self.imported_folder = folder
    
            print(f"Imported {len(songs)} songs.")
            print(f"Total songs: {len(self.music_files)}")
            self.refresh_playlist()
            # Change import button appearance    
            # Hide the large button
            self.import_button.pack_forget()
    
            # Show the small + button
            self.small_import_button.place(
                relx=0.92,
                rely=0.94,
                anchor="center"
            )
    def show_playlist(self):
        self.player.pack_forget()

        self.playlist_view.pack(
            padx=20,
            pady=20,
            fill="both",
            expand=True
        )

        self.refresh_playlist()

    def hide_playlist(self):
        """Return to main player."""

        self.playlist_view.pack_forget()

        self.player.pack(
            padx=20,
            pady=20,
            fill="both",
            expand=True
        )


    def refresh_playlist(self):
        """Rebuild the playlist UI."""

        # Remove existing rows
        for widget in self.playlist_scroll.winfo_children():
            widget.destroy()

        total_songs = len(self.music_files)

        self.song_count_label.configure(
            text=f"{total_songs} songs"
        )

        if total_songs == 0:

            empty_label = ctk.CTkLabel(
                self.playlist_scroll,
                text="No music imported",
                text_color="#777777",
                font=ctk.CTkFont(size=15)
            )

            empty_label.pack(
                pady=50
            )

            return

        # Create a row for every song
        for index, file_path in enumerate(self.music_files):

            self.create_song_row(
                index,
                file_path
            )


    def create_song_row(self, index, file_path):
        """Create one playlist row."""

        row = ctk.CTkFrame(
            self.playlist_scroll,
            height=58,
            corner_radius=12,
            fg_color="#252525"
        )

        row.pack(
            fill="x",
            pady=4
        )

        row.pack_propagate(False)

        # Song number
        number_label = ctk.CTkLabel(
            row,
            text=f"{index + 1:02}",
            width=35,
            text_color="#777777"
        )

        number_label.pack(
            side="left",
            padx=(10, 5)
        )

        # Song name
        filename = os.path.basename(file_path)

        song_name = os.path.splitext(filename)[0]

        song_label = ctk.CTkLabel(
            row,
            text=song_name,
            anchor="w",
            font=ctk.CTkFont(size=14)
        )

        song_label.pack(
            side="left",
            fill="x",
            expand=True
        )

        # Play indicator
        if index == self.current_song_index:

            playing_label = ctk.CTkLabel(
                row,
                text="♪",
                text_color="#5b9cff",
                font=ctk.CTkFont(size=18, weight="bold")
            )

            playing_label.pack(
                side="right",
                padx=15
            )

        # Make the whole row clickable
        row.bind(
            "<Button-1>",
            lambda event, i=index: self.play_song(i)
        )

        number_label.bind(
            "<Button-1>",
            lambda event, i=index: self.play_song(i)
        )

        song_label.bind(
            "<Button-1>",
            lambda event, i=index: self.play_song(i)
        )
        
    def play_song(self, index):
    #----- Load and play a song from the playlist. ----#

        if not self.music_files:
            return

        if index < 0 or index >= len(self.music_files):
            return

        file_path = self.music_files[index]

        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            self.current_song_index = index
            self.is_paused = False

            # Get duration
            try:
                sound = pygame.mixer.Sound(file_path)
                self.song_duration = sound.get_length()
            except Exception:
                self.song_duration = 0

            # Update song information
            filename = os.path.basename(file_path)
            song_name = os.path.splitext(filename)[0]

            self.song_title.configure(
                text=song_name
            )

            self.artist.configure(
                text="Unknown Artist"
            )

            # Change play button
            self.play_button.configure(
                text="❚❚"
            )

            # Refresh playlist
            self.refresh_playlist()

            # Start progress tracking
            self.update_progress()

        except Exception as error:

            print("Could not play song:")
            print(error)

if __name__ == "__main__":
    app = MusicPlayer()
    app.mainloop()
