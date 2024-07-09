import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from googleapiclient.discovery import build
import requests
import webbrowser 

# مجلد لحفظ الإعدادات
APP_DATA_FOLDER = os.path.join(os.getenv('APPDATA'), 'YouTubeThumbnailsDownloader')
if not os.path.exists(APP_DATA_FOLDER):
    os.makedirs(APP_DATA_FOLDER)

# استخدام مفتاح API الخاص بك
YOUTUBE_API_KEY_FILE = os.path.join(APP_DATA_FOLDER, 'youtube_api_key.txt')
if os.path.exists(YOUTUBE_API_KEY_FILE):
    with open(YOUTUBE_API_KEY_FILE, 'r') as f:
        YOUTUBE_API_KEY = f.read().strip()
else:
    YOUTUBE_API_KEY = '  🔑  أكتب مفتاح هنا   🔑    '

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

class YouTubeThumbnailsDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Thumbnails Downloader")
        self.geometry("600x400")
        self.configure(bg='#f0f0f0')
        self.resizable(False, False)  # تعيين النافذة كغير قابلة للتغيير الحجم


        # الخلفية الرئيسية
        bg_frame = tk.Frame(self, bg='#ffffff')
        bg_frame.pack(fill=tk.BOTH, expand=True)

        # عنوان التطبيق مع زر الإعدادات
        title_frame = tk.Frame(bg_frame, bg='#ffffff')
        title_frame.pack(pady=20)

        title_label = tk.Label(title_frame, text="YouTube Thumbnails Downloader", bg='#ffffff', fg='#333333', font=('Segoe UI', 18, 'bold'))
        title_label.pack(side=tk.LEFT, padx=10)

        settings_button = tk.Button(title_frame, text="︙", command=self.open_settings, font=('Segoe UI', 16), bg='#ffffff', relief=tk.FLAT)
        settings_button.pack(side=tk.RIGHT, padx=10)

        # مربع الإدخال لرابط القناة
        self.channel_url_entry = tk.Entry(bg_frame, width=50, bd=1, relief=tk.FLAT, font=('Segoe UI', 12), fg='#333333', bg='#f0f0f0')
        self.channel_url_entry.pack(pady=10)

        # زر لتحميل الصور المصغرة
        download_button = tk.Button(bg_frame, text="Download Thumbnails", command=self.start_download, bg='#0078D4', fg='#ffffff', bd=0, relief=tk.FLAT, font=('Segoe UI', 12))
        download_button.pack(pady=20)

        # شريط التقدم
        self.progress_bar = ttk.Progressbar(bg_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress_bar.pack(pady=20)

        # عداد عدد الفيديوهات
        self.video_count_label = tk.Label(bg_frame, text="", bg='#ffffff', fg='#333333', font=('Segoe UI', 12))
        self.video_count_label.pack(pady=10)

        # زر الرابط إلى الموقع
        link_button = tk.Button(bg_frame, text="@aio.Tv1", command=self.open_website, bg='#ffffff', fg='#0078D4', bd=0, relief=tk.FLAT, font=('Segoe UI', 12, 'underline'))
        link_button.pack(pady=10)

    def open_settings(self):
        new_api_key = simpledialog.askstring("API Settings", "Enter your YouTube Data API Key:", parent=self)
        if new_api_key:
            self.save_api_key(new_api_key)
            messagebox.showinfo("API Settings", "API Key saved successfully.")

    def save_api_key(self, api_key):
        with open(YOUTUBE_API_KEY_FILE, 'w') as f:
            f.write(api_key)
        global YOUTUBE_API_KEY
        YOUTUBE_API_KEY = api_key
        global youtube
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    def start_download(self):
        channel_url = self.channel_url_entry.get()
        if not channel_url:
            messagebox.showerror("Error", "Please enter a YouTube channel URL")
            return

        save_path = filedialog.askdirectory()
        if not save_path:
            messagebox.showerror("Error", "Please select a directory to save the thumbnails")
            return

        try:
            channel_id = self.get_channel_id(channel_url)
            playlist_id = self.get_uploads_playlist_id(channel_id)
            self.download_thumbnails(playlist_id, save_path)
            messagebox.showinfo("Success", "Thumbnails downloaded successfully.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def get_channel_id(self, channel_url):
        if 'channel/' in channel_url:
            return channel_url.split('channel/')[-1]
        elif 'user/' in channel_url:
            username = channel_url.split('user/')[-1]
            response = youtube.channels().list(forUsername=username, part='id').execute()
            return response['items'][0]['id']
        elif '@' in channel_url:
            username = channel_url.split('@')[-1]
            response = youtube.search().list(part='snippet', q=username, type='channel').execute()
            return response['items'][0]['snippet']['channelId']
        else:
            raise ValueError("Invalid YouTube channel URL")

    def get_uploads_playlist_id(self, channel_id):
        response = youtube.channels().list(part='contentDetails', id=channel_id).execute()
        return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    def get_video_count(self, playlist_id):
        response = youtube.playlistItems().list(part='snippet', playlistId=playlist_id, maxResults=50).execute()
        return response['pageInfo']['totalResults']

    def download_thumbnails(self, playlist_id, save_path):
        next_page_token = None
        video_count = 0
        total_videos = self.get_video_count(playlist_id)
        self.progress_bar['maximum'] = total_videos

        while True:
            response = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            for item in response.get('items', []):
                thumbnail_url = item['snippet']['thumbnails']['high']['url']
                video_id = item['snippet']['resourceId']['videoId']
                thumbnail_path = os.path.join(save_path, f'{video_id}.jpg')
                self.download_image(thumbnail_url, thumbnail_path)

                video_count += 1
                self.progress_bar['value'] = video_count
                self.video_count_label.config(text=f"Downloaded {video_count} of {total_videos} videos")
                self.update_idletasks()

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

    def download_image(self, url, path):
        response = requests.get(url)
        if response.status_code == 200:
            with open(path, 'wb') as file:
                file.write(response.content)

    def open_website(self):
        webbrowser.open("https://oussamaidiken.framer.website/")

app = YouTubeThumbnailsDownloader()
app.mainloop()
