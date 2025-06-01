import requests
import json
import time
from collections import defaultdict, deque
import networkx as nx
import matplotlib.pyplot as plt

# Import podcast data from Taddy.org
# Set headers to authenticate request
headers = {
    "Content-Type": "application/json",
    "X-USER-ID": "2670",
    "X-API-KEY": "51ce7904d50c858cba100a2f8c364d390204aae0c4f069e4de2908846975590582199e43dfed008edb5b94d2f7055542ee",
}

# Country to fetch data from
country = "UNITED_STATES_OF_AMERICA"

# Fetch data from multiple pages
limitPerPage = 25
maxPages = 10

# Initialize an empty list 
allPodcasts = []

print(f"Fetching podcasts from: {country}")

for page in range(1, maxPages + 1):
    print(f"Requesting page {page} ")

# Define GraphQL query
    query = f"""
    query {{
        getTopChartsByCountry(taddyType: PODCASTSERIES, country: {country},
        page: {page},
        limitPerPage: {limitPerPage}
        ){{
        topChartsId
        podcastSeries{{
        uuid
        name
        genres
        }}
        }}
        }}
    """
# Send POST request
    response = requests.post("https://api.taddy.org/graphql",
                            headers=headers,
                            json={"query": query}
                            )
    # Check if the response is successful
    if response.status_code != 200:
        print(f"Request failed on page {page}: {response.status_code}")
        print("Response content:", response.text)
        break
    try:
        data = response.json()
        podcasts = data["data"]["getTopChartsByCountry"]["podcastSeries"]
    except Exception as e:
        print(f"Error parsing JSON on page {page}. Ending pagination.")
        break
    for podcast in podcasts:
        if podcast.get("genres"):
            allPodcasts.append({
                "title": podcast["name"],
                "genres": podcast["genres"],
                "country": country
            })
    time.sleep(1)

# Save results
outputFile = "top_US_podcasts.json"
with open(outputFile, "w", encoding="utf-8") as f:
    json.dump(allPodcasts, f, indent=2)

print(f"Saved {len(allPodcasts)} podcasts to {outputFile}")

# Begin building genre co-occurrence graph by defining a class
class PodcastGenreGraph:
    def __init__(self, json_file):
        self.adjList = defaultdict(dict) # Initialize an adjacency dictionary
        self.loadData(json_file) # Load graph data from JSON file

    def loadData(self, json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            podcastData = json.load(f)

        for podcast in podcastData:
            genres = podcast.get("genres", [])
            for i in range(len(genres)):
                for j in range(i + 1, len(genres)):
                    g1, g2 = genres[i], genres[j]

                # update both directions in the adjacency list
                    if g2 not in self.adjList[g1]:
                     self.adjList[g1][g2] = 1
                    else:
                        self.adjList[g1][g2] += 1
                    if g1 not in self.adjList[g2]:
                        self.adjList[g2][g1] = 1
                    else:
                        self.adjList[g2][g1] += 1

    def calcShortestPath(self, start, end):
        if start not in self.adjList or end not in self.adjList:
            return [-1, []]
        if start == end:
            return [0, [start]]
        
        visited = set()
        queue = deque([start])
        parent = {}

        visited.add(start)

        while queue:
            current = queue.popleft()
            for neighbor in self.adjList[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current 
                    queue.append(neighbor)
                    if neighbor == end:
                        path = [end]
                        while path[-1] != start:
                            path.append(parent[path[-1]])
                        path.reverse()
                        return [len(path) - 1, path]
        return [-1, []]
    
    def printAdjList(self):
        for genre, neighbors in self.adjList.items():
            print(f"{genre}: {neighbors}")

    def topConnectedGenres(self, top_n=10):
        """
        This will return the top N genres by number of direct connections (degree centrality).
        """
        degreeCounts = {genre: len(neighbors) for genre, neighbors in self.adjList.items()}
        sortedGenres = sorted(degreeCounts.items(), key=lambda x: x[1], reverse=True)
        return sortedGenres[:top_n]
    
    def VisualizeGraph(self, top_n=30):
        """
        Visualizes the graph using networkx. Only includes the top N genres by degree.
        """
        topGenres = {genre for genre, _ in self.topConnectedGenres(top_n)}
        G = nx.Graph()

        # Add nodes and edges (with weights)
        for genre in topGenres:
            for neighbor, weight in self.adjList[genre].items():
                if neighbor in topGenres:
                    G.add_edge(genre.replace("PODCASTSERIES_", ""), 
                               neighbor.replace("PODCASTSERIES_", ""), weight=weight)
                    
        # Use Kamada-Kawai layout for better spacing            
        pos = nx.kamada_kawai_layout(G)

        # Normalize edge widths
        rawWeights = [G[u][v]["weight"] for u, v in G. edges()]
        max_w = max(rawWeights) if rawWeights else 1
        edgeWeights = [1 + (5 * w / max_w) for w in rawWeights]

        plt.figure(figsize=(14,10))
        nx.draw_networkx_nodes(G, pos, node_color="skyblue", node_size=800)
        nx.draw_networkx_edges(G, pos, width=edgeWeights)
        nx.draw_networkx_labels(G, pos, font_size=8, font_weight="bold")
        plt.title(f"Top {top_n} Podcast Genre Co-occurrences", fontsize=14)
        plt.axis("off")
        plt.tight_layout()
        plt.show()


def main_menu():
        current_file = "top_US_podcasts.json"
        try:
            g = PodcastGenreGraph(current_file)
        except Exception as e:
            print(f"Failed to load dataset: {e}")
            return
        while True:
            print("\n ==== Podcast Genre Network Menu =====")
            print("1. Find shortest path between two genres")
            print("2. Show most connected genres")
            print("3. Visualize graph")
            print("4. Quit")
            choice = input("Enter your choice (1-4): ").strip()

            if choice == "1":
                src = "PODCASTSERIES_" + input("Enter starting genre (e.g., COMEDY): ").strip().upper()
                dst = "PODCASTSERIES_" + input("Enter destination genre (e.g., TRUE_CRIME): ").strip().upper()
                path_length, path = g.calcShortestPath(src, dst)
                if path_length == -1:
                    print("No path found between those genres.")
                else:
                    print(f"\nShortest path between {src} and {dst} (length {path_length}): ")
                    print(" --> ".join(str(genre) for genre in path))

            elif choice == "2":
                try:
                    n = int(input("How many top genres do you want to show? "))
                except ValueError:
                    print("Please enter a valid number.")
                    continue
                print(f"\nTop {n} most connected genres:")
                for genre, degree in g.topConnectedGenres(n):
                    print(f"{genre}: connected to {degree} genres")

            elif choice == "3":
                try:
                    n = int(input("How many top genres do you want to include in the visualization? "))
                    g.VisualizeGraph(top_n=n)
                except Exception as e:
                    print(f"Could not visualize graph {e}")

            elif choice == "4":
                print("Okay! Goodbye!")
                break
            
            else:
                print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
        main_menu()


# Test the graph
# if __name__ == "__main__":
#     g = PodcastGenreGraph("top_US_podcasts.json")
#     g.printAdjList

#     # Example shortest path 
#     # start = "PODCASTSERIES_COMEDY"
#     # end = "PODCASTSERIES_TRUE_CRIME"
#     # path_len, path = g.calcShortestPath(start, end)
#     # print({f"\nShortest path between {start} and {end} (length {path_len}): "})
#     # print(" -> ".join(path) if path else "No path found")

#     # Print top 10 genre with highest degree
#     # print("\nTop 10 most interconnected genres (by degree): ")
#     # for genre, degree in g.topConnectedGenres(10):
#     #     print(f"{genre}: connected to {degree} genres")

#     # Visualize graph
#     g.VisualizeGraph(top_n=30)