
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import threading
import numpy as np

# Configuration parameters for columns and rows
num_columns = 4  # Number of streams per row
num_rows = 3  # Number of rows

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


class StreamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RTSP Streams Viewer")

        self.frame = ttk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        self.stream_labels = []
        self.active_stream_label = None
        self.running_threads = {}

        # Create stream labels in a grid
        for r in range(num_rows):
            for c in range(num_columns):
                index = r * num_columns + c
                if index < len(rtsp_streams):
                    key = list(rtsp_streams.keys())[index]
                    self.create_stream_label(r, c, key)

    def create_stream_label(self, row, column, key):
        stream_frame = ttk.Frame(self.frame)
        stream_frame.grid(row=row, column=column, padx=5, pady=5)

        stream_label = ttk.Label(stream_frame, text=f"Stream: {key}")
        stream_label.pack()

        rtsp_label = ttk.Label(stream_frame)
        rtsp_label.pack()

        rtsp_label.bind("<Button-1>", lambda event, lbl=rtsp_label: self.on_label_click(event, lbl))

        self.stream_labels.append((rtsp_label, key))

        # Start thread for reading video stream
        stream_url = rtsp_streams[key]["stream"]
        stop_event = threading.Event()
        active_thread = threading.Thread(target=self.read_video_stream, args=(stream_url, rtsp_label, stop_event))
        self.running_threads[rtsp_label] = (active_thread, stop_event)
        active_thread.daemon = True
        active_thread.start()

    def read_video_stream(self, stream_url, rtsp_label, stop_event):
        rtsp_stream = cv2.VideoCapture(stream_url)
        if rtsp_stream.isOpened():
            while not stop_event.is_set():
                ret, frame = rtsp_stream.read()
                if not ret:
                    break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (350, 170))
                frame_image = Image.fromarray(frame)
                frame_image = ImageTk.PhotoImage(frame_image)
                rtsp_label.configure(image=frame_image)
                rtsp_label.image = frame_image
                self.root.update_idletasks()  # Ensure the label updates
        rtsp_stream.release()

    def on_label_click(self, event, clicked_label):
        print("Label clicked!")  # Debug statement
        if self.active_stream_label == clicked_label:
            # If the same label is clicked again, reset all labels
            self.active_stream_label = None
            for label, key in self.stream_labels:
                # Restart the threads for all streams
                thread, stop_event = self.running_threads[label]
                stop_event.set()
                new_thread = threading.Thread(target=self.read_video_stream, args=(rtsp_streams[key]["stream"], label, stop_event))
                self.running_threads[label] = (new_thread, stop_event)
                new_thread.daemon = True
                new_thread.start()
        else:
            self.active_stream_label = clicked_label
            for label, key in self.stream_labels:
                if label != clicked_label:
                    # Stop the threads for all other streams
                    thread, stop_event = self.running_threads[label]
                    stop_event.set()
                    # Set other labels to show a black screen
                    black_frame = np.zeros((170, 300, 3), dtype=np.uint8)
                    black_image = Image.fromarray(black_frame)
                    black_image = ImageTk.PhotoImage(black_image)
                    label.configure(image=black_image)
                    label.image = black_image

if __name__ == "__main__":
    root = tk.Tk()
    app = StreamApp(root)
    root.mainloop()
