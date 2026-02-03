# Darts Scorer

A LOCAL web-based darts scoring application built with Flask and Tailwind CSS.

## Features

- **X01 Game Mode**: Standard 501/301 scoring with checkout suggestions and average tracking.
- **Practice 20 Mode**: Practice hitting the 20 segment with detailed statistics and visualization.
- **Multiplayer Support**: Play with multiple players locally.
- **Responsive Design**: Optimized for both desktop and tablet/mobile use.

## Prerequisites

- Python 3.x
- Node.js & npm (for building Tailwind CSS)

## Installation

1.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install Node.js dependencies**:
    ```bash
    npm install
    ```

## Running the Application

1.  **Build the CSS**:
    You need to generate the CSS file using Tailwind before running the app.
    ```bash
    npm run build:css
    ```
    *Optional: Use `npm run watch:css` to automatically rebuild CSS when you make changes.*

2.  **Start the Flask server**:
    ```bash
    python app.py
    ```

3.  **Open in Browser**:
    Go to `http://localhost:5000` (or the local IP address displayed in your terminal) to start the game.