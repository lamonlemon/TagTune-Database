# TagTune Database PRD

## Need Tools

1. Supabase + PostgreSQL
2. Youtube v3 api (Public)
3. Gemini API
4. ytmusicapi (python library)

## Rogic 1 (Only original songs)

1. Put playlist to the code
2. Get video link in the playlist by Youtube v3 API
3. Get Artist & Title & Album & Publish Year of video by ytmusicapi
4. Repeat 2~3 for all videos
5. Make prompt for AI by adding songs from 2~4 by title-artist formet below

```
────────────────────────
[INPUT]
────────────────────────
```

of @base_prompt.txt by index 1. 2. 3. 4. ...

1. Put 5. prompt to llm api and get json
2. Add title, artist number, url to json which AI given

```
[
  {
    "index": 1,
    "title": "Seven (feat. Latto)",
    "artist": "Jung Kook",
    "group": "BTS",
    "genre": [2, 12, 21],
    "release_year": 2023,
    "featuring": ["Latto"],
    "producer": [],
    "language": "English",  
    "url": "https://music.youtube.com/watch?v=Vs64cZbeY88"
    "confident": "3"
  }
]
````

1. Put data from 3, 7 to the database.

## Rogic 2 (Cover)

1. Put playlist to the code
2. Get video link in the playlist
3. Get metadata of video by Youtube v3 api
4. Check is the song is cover by find word on title such as [cover, 커버, ...]
5. Link to original song and put it in table.
6. Use channel name to get artist
7. Put the album_id and release_year `NULL`

## DB Tree

```
songs
 ├── song_index
 ├── title
 ├── original_song_id (PK) ────────┐
 ├── artist_id ───────────────────┐│
 ├── album_id ───────────────────┐││
 ├── group_id (nullable) ───────┐│││
 ├── release_year               ││││
 └── url                        ││││
                                ││││
artists                         ││││
 ├── artist_id (PK) ◀───────────┘│││
 └── name                        │││
                                 │││
groups                           │││
 ├── group_id (PK) ◀─────────────┘││
 └── name                         ││
                                  ││
albums                            ││
 ├── album_id (PK) ◀──────────────┘│
 ├── title                         │
 └── artist_id (FK)                │
                                   │
song_featuring                     │
 ├── song_id (FK)                  │
 └── artist_id (FK)                │
                                   │
song_producers                     │
 ├── song_id (FK)                  │
 └── artist_id (FK)                │
                                   │
song_genres                        │
 ├── song_id (FK) ◀────────────────┘
 ├── primary_genre_id (FK)
 ├── sub_genre_id (FK)
 └── micro_genre_id (FK)

genres
 ├── genre_id (PK)
 ├── name
 ├── level (1=primary, 2=sub, 3=micro)
```

### For Ex)  

Jung Kook - Seven (feat. Latto)

### songs

|song_index | title | artist_id | group_id | album_id | release_year | url | original_song_id |
|-|-|-|-|-|-|-|-|
|1 | Seven (feat. Latto) | 10 | 3 | 1 | 2023 | <https://music.youtube.com/watch?v=Vs64cZbeY88> | 1 |
|...|....|...|...|...|...|...|...|

(if song is original song, put original_song_id to same as song_id)
(if song is corver song, put `original_song_id` to origninal song's `song_index`)

### artists

|artist_id|name|
|---|--|
|...|....|
|10 |Jung Kook|
|11 |Latto|
|...|....|

### groups

|group_id|name|
|-|-|
|...|...|
|3|BTS|

### song_featuring

|song_id|artist_id|
|-|-|
|1 |11|
|...|...|

### song_producers

|song_id|artist_id|
|-|-|
|1 |  |
|...|...|

### song_genres

|song_id|primary|sub|micro|
|-|-|-|-|
|1|13|150|1050|
|...|...|

(song_id is from tabel songs, original_song_id)

### genre

|genre_id|name|level|
|-|-|-|
|...|...|...|
|13|K-pop|1|
|...|...|...|
|150|Dance Pop|2|
|...|...|...|
|1050|City Pop|3|
|...|...|...|
