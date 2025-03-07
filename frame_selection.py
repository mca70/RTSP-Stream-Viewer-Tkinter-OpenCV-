import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import threading
import time

rtsp_streams = {
    "30": {"stream": "rtsp://admin:Admin123@192.168.0.116:554/Streaming/channels/102", "ip_address": ""},
    "31": {"stream": "rtsp://admin:Admin123@192.168.0.114:554/Streaming/channels/102", "ip_address": ""},
    "32": {"stream": "rtsp://admin:Admin123@192.168.0.118:554/Streaming/channels/102", "ip_address": ""},
    "33": {"stream": "rtsp://admin:Admin123@192.168.0.121:554/Streaming/channels/102", "ip_address": ""},
    "34": {"stream": "rtsp://admin:Admin123@192.168.0.122:554/Streaming/channels/102", "ip_address": ""},
    "40": {"stream": "rtsp://admin:Admin123@192.168.0.119:554/Streaming/channels/102", "ip_address": ""},
    "41": {"stream": "rtsp://admin:Admin123@192.168.0.126:554/Streaming/channels/102", "ip_address": ""},
    "42": {"stream": "rtsp://admin:Admin123@192.168.0.115:554/Streaming/channels/102", "ip_address": ""},
    "43": {"stream": "rtsp://admin:Admin123@192.168.0.124:554/Streaming/channels/102", "ip_address": ""},
}


# Configuration parameters for columns and rows
num_columns = 3  # Number of streams per row
num_rows = 3  # Number of rows

window_width = 400
window_height = 200

class StreamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RTSP Streams Viewer")

        self.frame = ttk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        self.stream_labels = []
        self.black_screen_flag = {key: False for key in rtsp_streams}

        # Create a black image for the placeholder
        self.black_image = ImageTk.PhotoImage(Image.new("RGB", (window_width, window_height), "black"))

        # Create stream labels in a grid
        stream_keys = list(rtsp_streams.keys())
        for r in range(num_rows):
            for c in range(num_columns):
                index = r * num_columns + c
                if index < len(stream_keys):
                    stream_key = stream_keys[index]
                    self.create_stream_label(r, c, stream_key)

        # Add button to toggle black screen
        self.black_screen_button = ttk.Button(self.root, text="Toggle Black Screen", command=self.toggle_black_screen)
        self.black_screen_button.pack(side=tk.TOP, padx=10, pady=5)

    def create_stream_label(self, row, column, stream_key):
        stream_frame = ttk.Frame(self.frame)
        stream_frame.grid(row=row, column=column, padx=5, pady=5)

        stream_label = ttk.Label(stream_frame, text=f"Stream: {stream_key}")
        stream_label.pack()

        rtsp_label = ttk.Label(stream_frame)
        rtsp_label.pack()

        self.stream_labels.append((stream_key, rtsp_label))

        # Bind click event to display black screen
        rtsp_label.bind("<Button-1>", lambda event, lbl=rtsp_label, key=stream_key: self.toggle_individual_black_screen(lbl, key))

        # Start thread for reading video stream
        stream_url = rtsp_streams[stream_key]["stream"]
        active_thread = threading.Thread(target=self.read_video_stream, args=(stream_url, rtsp_label, stream_key))
        active_thread.daemon = True
        active_thread.start()

    def toggle_individual_black_screen(self, label, stream_key):
        self.black_screen_flag[stream_key] = not self.black_screen_flag[stream_key]
        if self.black_screen_flag[stream_key]:
            label.configure(image=self.black_image)
            label.image = self.black_image
        else:
            stream_url = rtsp_streams[stream_key]["stream"]
            active_thread = threading.Thread(target=self.read_video_stream, args=(stream_url, label, stream_key))
            active_thread.daemon = True
            active_thread.start()

    def toggle_black_screen(self):
        for stream_key, label in self.stream_labels:
            self.toggle_individual_black_screen(label, stream_key)

    def read_video_stream(self, stream_url, rtsp_label, stream_key):
        while True:
            if self.black_screen_flag[stream_key]:
                rtsp_label.configure(image=self.black_image)
                rtsp_label.image = self.black_image
                time.sleep(0.1)  # Sleep to reduce CPU usage
                continue

            rtsp_stream = cv2.VideoCapture(stream_url)
            if rtsp_stream.isOpened():
                while not self.black_screen_flag[stream_key]:
                    ret, frame = rtsp_stream.read()
                    if not ret:
                        break
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (window_width, window_height))
                    frame_image = Image.fromarray(frame)
                    frame_image = ImageTk.PhotoImage(frame_image)
                    rtsp_label.configure(image=frame_image)
                    rtsp_label.image = frame_image
                rtsp_stream.release()
            else:
                print(f"Failed to open stream {stream_key}")
                time.sleep(1)  # Wait before retrying

if __name__ == "__main__":
    root = tk.Tk()
    app = StreamApp(root)
    root.mainloop()
