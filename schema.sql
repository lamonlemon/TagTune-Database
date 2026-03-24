-- schema.sql for TagTune Database

-- 1. Create Genres table
CREATE TABLE IF NOT EXISTS genres (
    genre_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    level INTEGER NOT NULL -- 1=primary, 2=sub, 3=micro
);

-- 2. Create Artists table
CREATE TABLE IF NOT EXISTS artists (
    artist_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- 3. Create Groups table
CREATE TABLE IF NOT EXISTS groups (
    group_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- 4. Create Albums table
CREATE TABLE IF NOT EXISTS albums (
    album_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    artist_id INTEGER REFERENCES artists(artist_id),
    UNIQUE(title, artist_id)
);

-- 5. Create Songs table
CREATE TABLE IF NOT EXISTS songs (
    song_index SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    original_song_id INTEGER, -- Self-reference or link to original song_index
    artist_id INTEGER REFERENCES artists(artist_id),
    album_id INTEGER REFERENCES albums(album_id),
    group_id INTEGER REFERENCES groups(group_id),
    release_year INTEGER,
    url TEXT UNIQUE,
    language TEXT
);

-- Note: original_song_id logic:
-- If original song: original_song_id = song_index (self)
-- If cover song: original_song_id = index of original song
ALTER TABLE songs 
ADD CONSTRAINT fk_original_song 
FOREIGN KEY (original_song_id) REFERENCES songs(song_index);

-- 6. Create Song Featuring table
CREATE TABLE IF NOT EXISTS song_featuring (
    song_id INTEGER REFERENCES songs(song_index),
    artist_id INTEGER REFERENCES artists(artist_id),
    PRIMARY KEY (song_id, artist_id)
);

-- 7. Create Song Producers table
CREATE TABLE IF NOT EXISTS song_producers (
    song_id INTEGER REFERENCES songs(song_index),
    artist_id INTEGER REFERENCES artists(artist_id),
    PRIMARY KEY (song_id, artist_id)
);

-- 8. Create Song Genres table
CREATE TABLE IF NOT EXISTS song_genres (
    song_id INTEGER PRIMARY KEY REFERENCES songs(song_index),
    primary_genre_id INTEGER REFERENCES genres(genre_id),
    sub_genre_id INTEGER REFERENCES genres(genre_id),
    micro_genre_id INTEGER REFERENCES genres(genre_id)
);