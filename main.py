from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import html

from badwords import search_bad_words

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def search_page():
    return """
    <html>
    <head>
        <title>Bad Word Search</title>
        <script src="https://unpkg.com/vue@3"></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .video-item {
                position: relative;
            }

            .preview {
                position: absolute;
                left: 120px;
                top: -20px;
                width: 200px;

                opacity: 0;
                transform: scale(0.95) translateY(5px);
                transition: opacity 0.25s ease, transform 0.25s ease;

                pointer-events: none;
            }

            .video-item:hover .preview {
                opacity: 1;
                transform: scale(1) translateY(0);
            }

            .preview img {
                width: 100%;
            }

            .fade-in {
                opacity: 0;
                transform: translateY(10px);
                animation: fadeIn 0.8s ease forwards;
            }

            .fade-enter-active {
                transition: all 0.3s ease;
                transition-delay: calc(var(--i) * 0.03s);
            }

            .fade-enter-from {
                opacity: 0;
                transform: translateY(8px);
            }

            .fade-enter-to {
                opacity: 1;
                transform: translateY(0);
            }

            .delay-1 { animation-delay: 0.2s; }
            .delay-2 { animation-delay: 0.4s; }
            .delay-3 { animation-delay: 0.6s; }

            @keyframes fadeIn {
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        </style>
    </head>
    <body>

    <div id="app" class="min-h-screen bg-gray-900 text-white flex flex-col items-center p-10">

    <h1 class="text-4xl font-bold mb-6">YouTube ID Search</h1>
    <div class="text-gray-400 mb-6 max-w-xl text-center space-y-2">
        <p class="fade-in delay-1">Youtube video IDs are made of random 11 character sequences.</p>
        <p class="fade-in delay-2">That means that out of 1 million video IDs, the probability of a 3 or 4 letter word showing up is near 1. I've collected 1 million video IDs to test the results.</p>
        <p class="fade-in delay-3">This tool compares observed frequency vs theoretical probability.</p>
    </div>
    <div class="flex gap-2 mb-6">
        <input v-model="query"
               class="p-2 rounded text-black w-64"
               placeholder="Enter word..." />

        <button @click="search(1)"
                class="bg-red-500 px-4 py-2 rounded hover:bg-red-600">
            Search
        </button>
    </div>

    <div v-if="loading" class="mb-4">Loading...</div>

    <div v-if="stats" class="mb-4 text-gray-300">
        Total: {{ stats.total }} |
        Matches: {{ stats.matches }} |
        Expected Matches: {{ stats.expected_matches }} |
        Difference: {{ stats.difference }} |
        Accuracy diff: {{stats.percent_difference > 0 ? '+' : ''}} {{ stats.percent_difference.toFixed(2) }}%
    </div>

    <p v-if="stats && stats.matches === 0" class="text-gray-400">
        No results found
    </p>

    <ul class="space-y-2">
        <transition-group name="fade" tag="ul" class="space-y-2">
            <li v-for="(vid, index) in results" :key="vid" class="video-item" :style="{ '--i': index}">
                <a class="text-blue-400 hover:underline"
                :href="'https://www.youtube.com/watch?v=' + vid"
                target="_blank">
                    {{ vid }}
                </a>
                <div class="preview">
                    <img :src="'https://img.youtube.com/vi/' + vid + '/0.jpg'" />
                </div>
            </li>
        </transition-group>
    </ul>

    <div class="mt-6 flex gap-4">
        <button @click="prevPage"
                class="px-4 py-2 bg-gray-700 rounded disabled:opacity-50"
                :disabled="page === 1">
            Prev
        </button>

        <button @click="nextPage"
                class="px-4 py-2 bg-gray-700 rounded disabled:opacity-50"
                :disabled="!hasMore">
            Next
        </button>
    </div>

</div>

    <script>
    const { createApp } = Vue;

    createApp({
        data() {
            return {
                query: "",
                results: [],
                stats: null,
                page: 1,
                loading: false,
                hasMore: true
            };
        },

        methods: {
            async search(page = 1) {
                if (!this.query.trim()) return;

                this.page = page;
                this.loading = true;

                try {
                    const res = await fetch(`/search?q=${this.query}&page=${this.page}`);
                    const data = await res.json();

                    this.results = data.results;
                    this.stats = data;

                    const maxShown = this.page * 50;
                    this.hasMore = maxShown < data.matches;

                } catch (err) {
                    console.error(err);
                }

                this.loading = false;
            },

            nextPage() {
                if (!this.query) return;
                this.search(this.page + 1);
            },

            prevPage() {
                if (this.page > 1) {
                    this.search(this.page - 1);
                }
            }
        }
    }).mount("#app");
    </script>

    </body>
    </html>
    """

@app.get("/search")
def search_api(q: str = "", page: int = 1): 
    limit = 50
    query_length = len(q)
    k = 11 - query_length + 1 #number of positions it can appear in
    results, total, match_count = ( 
        search_bad_words(q, page, limit) if q else ([], 0, 0)
       )
    variants = 2**query_length #since the search is case insensitive, we have to calculcate for variance of each character
    probability = 1 - (1 - (variants/(64 ** query_length))) ** k if q else 0
    expected_matches = round(probability * total)
    difference = match_count - expected_matches
    percent_difference = ( ((match_count - expected_matches) / expected_matches) * 100
                          if expected_matches > 0 else 0
                          )
    return { 
      "query": q,
      "page": page,
      "limit": limit,
      "results": results,
      "total": total,
      "matches": match_count,
      "expected_matches": expected_matches,
      "difference": difference,
      "percent_difference": percent_difference,
      "percentage": (match_count / total * 100) if total else 0,
      "probability": probability
    }