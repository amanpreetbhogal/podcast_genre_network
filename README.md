# 🎧 Podcast Genre Ecosystem - Mapping a Network of Trendy Genres

This project explores how podcast genres relate to one another by building a graph-based network from real-time podcast data retrieved from the [Taddy.org's Podcast GraphQL API](https://taddy.org/developers/podcast-api). By analyzing co-occurring genres in trending podcasts, this tool helps visualize and explore connections across the podcast landscape.

## 📌 Project Overview

- **Goal**: Identify relationships between podcast genres using a graph data structure.
- **Data Source**: Taddy.org’s GraphQL API (top charted podcasts in the U.S.).
- **Graph Logic**:
  - Each **genre** is a node.
  - An **edge** connects two genres if they co-occur in the same podcast.
  - Edges are **weighted** based on how often the genres appear together.

## 🧠 Features

- **Shortest Path Search**: Use Breadth-First Search (BFS) to find the shortest connection between any two genres.
- **Top Connected Genres**: Display the top N genres with the highest number of connections (degree centrality).
- **Graph Visualization**: View an interactive graph with nodes and weighted edges using `networkx` and `matplotlib`.
- **Command Line Interface**: Navigate the program through a clear CLI menu.
