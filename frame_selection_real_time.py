import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from threading import Thread
from queue import Queue
from collections import deque

class RTSPDisplayApp:
    def __init__(self, master, rtsp_streams):
        self.master = master
        self.rtsp_streams = rtsp_streams
        self.caps = [cv2.VideoCapture(stream) for stream in rtsp_streams]
        self.frames = []

        self.last_frames = [deque(maxlen = 50) for _ in range(len(rtsp_streams))]
        self.last_frames_resized = [deque(maxlen = 50) for _ in range(len(rtsp_streams))]
        self.frames_on_pop_up = []
        self.frames_on_pop_up_resized = []
        
        self.resized_width = 320
        self.resized_height = 240

        # Queue for communicating between threads and Tkinter
        self.queue = Queue()

        self.create_widgets()
        self.update_streams()

    def create_widgets(self):
        self.frames_container = tk.Frame(self.master)
        self.frames_container.pack()

        rows = 3  # Number of rows
        cols = (len(self.rtsp_streams) + rows - 1) // rows  # Number of columns

        self.frames = []
        for i in range(rows):
            for j in range(cols):
                index = i * cols + j
                if index >= len(self.rtsp_streams):
                    break

                frame = tk.Label(self.frames_container)
                frame.grid(row=i, column=j, padx=5, pady=5)
                self.frames.append(frame)

                # Bind mouse click event to show pop-up window
                frame.bind("<Button-1>", lambda event, idx=index: self.on_stream_click(idx))

                # Focus the label to capture key events
                frame.focus_set()

    def update_streams(self):
        for i, cap in enumerate(self.caps):
            # Start a new thread for each stream
            thread = Thread(target=self.update_stream, args=(i,))
            thread.start()

    def update_stream(self, stream_idx):
        cap = self.caps[stream_idx]
        while True:
            ret, frame = cap.read()

            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                original_frame = frame.copy()

                frame = cv2.resize(frame, (self.resized_width, self.resized_height))  # Resize frame
                self.queue.put((stream_idx, frame))

                original_frame = Image.fromarray(original_frame)
                self.last_frames[stream_idx].append(original_frame)

    def process_frame(self):
        while True:
            stream_idx, frame = self.queue.get()
            frame = Image.fromarray(frame)
            frame = ImageTk.PhotoImage(frame)

            # Update the label with the new frame
            self.frames[stream_idx].configure(image=frame)
            self.frames[stream_idx].image = frame
            self.last_frames_resized[stream_idx].append(frame)

    def on_stream_click(self, stream_idx):
        self.frames_on_pop_up_resized = list(self.last_frames_resized[stream_idx])
        self.frames_on_pop_up = list(self.last_frames[stream_idx])
        
        print(len(frames_on_pop_up_resized))

        self.popup = tk.Toplevel()
        self.popup.title(f"Stream {stream_idx + 1}, Select any frame to continue")
        self.popup.configure(background='gray')
    
        window_frames = [i for i in range(2, 50, 5)]
        print(window_frames)
        for i, frame in enumerate(self.frames_on_pop_up_resized):
            if i + 1 not in window_frames:
                continue
            row = i // 4
            col = i % 4
            label = tk.Label(self.popup, image=frame, bg='yellow')
            label.grid(row=row, column=col, padx=5, pady=5)

            # Bind mouse click event
            label.bind("<Button-1>", lambda event, idx=i: self.draw_circle(event, stream_idx, idx))

            # Bind key events
            label.focus_set()  # To make sure label gets the focus
            label.bind("<Key>", lambda event, idx=i: self.on_key_press(event, stream_idx, idx))


    def draw_circle(self, event, stream_idx, frame_idx):
        # Get the coordinates of the mouse click
        click_x, click_y = event.x, event.y

        # Save the click coordinates for later use
        self.last_click_x, self.last_click_y = click_x, click_y

        # Get the frame data from frames_on_pop_up
        frame_data = self.frames_on_pop_up_resized[frame_idx]

        # Update the frame label with the same image (without drawing the circle)
        frame_label = self.popup.grid_slaves(row=frame_idx // 4, column=frame_idx % 4)[0]
        frame_label.configure(image=frame_data)
        frame_label.image = frame_data  # Keep a reference to the image

        # Focus the label to capture key events
        frame_label.focus_set()
        frame_label.bind("<Key>", lambda event, idx=frame_idx: self.on_key_press(event, stream_idx, frame_idx))



    def on_key_press(self, event, stream_idx, frame_idx):
        # Get the key pressed
        key = event.char.lower()

        # Check if the key is valid
        if key in ['a', 's', 'd', 'f']:
            self.save_frame(stream_idx, frame_idx, key)
        elif key == '\x1b':  # Escape key
            self.popup.destroy()

    def save_frame(self, stream_idx, frame_idx, key):
        # Get the frame data from frames_on_pop_up
        original_frame_data = self.frames_on_pop_up[frame_idx]

        # Get the original frame size
        original_width, original_height = original_frame_data.width, original_frame_data.height

        # Calculate the resizing ratio
        resize_ratio_x = original_width / self.resized_width
        resize_ratio_y = original_height / self.resized_height

        # Calculate the original click coordinates
        original_click_x = self.last_click_x * resize_ratio_x
        original_click_y = self.last_click_y * resize_ratio_y

        # Draw a circle on the original size image
        draw = ImageDraw.Draw(original_frame_data)
        radius = 15
        draw.ellipse((original_click_x - radius, original_click_y - radius,
                      original_click_x + radius, original_click_y + radius), outline="red", width=2)

        # Save the modified image with original quality and format
        filename = f"stream_{stream_idx + 1}_frame_{frame_idx + 1}_key_{key}.jpg"
        original_frame_data.save(filename, format="JPEG", quality=100)

        # Close the popup window and clear the frames
        self.popup.destroy()
        self.frames_on_pop_up.clear()
        self.frames_on_pop_up_resized.clear()



if __name__ == "__main__":
    rtsp_streams = [
        "rtsp://admin:Admin123@192.168.0.116:554/Streaming/channels/102",
        "rtsp://admin:Admin123@192.168.0.114:554/Streaming/channels/102",
        "rtsp://admin:Admin123@192.168.0.118:554/Streaming/channels/102",
        "rtsp://admin:Admin123@192.168.0.121:554/Streaming/channels/102",
        "rtsp://admin:Admin123@192.168.0.122:554/Streaming/channels/102",
        "rtsp://admin:Admin123@192.168.0.119:554/Streaming/channels/102",
        "rtsp://admin:Admin123@192.168.0.126:554/Streaming/channels/102",
        "rtsp://admin:Admin123@192.168.0.115:554/Streaming/channels/102",
        "rtsp://admin:Admin123@192.168.0.124:554/Streaming/channels/102"
    ]

    root = tk.Tk()
    root.title("Screen Selection Theft")

    app = RTSPDisplayApp(root, rtsp_streams)

    # Start the frame processing thread
    frame_thread = Thread(target=app.process_frame)
    frame_thread.start()

    root.mainloop()
