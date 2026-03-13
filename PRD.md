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

```text
────────────────────────
[INPUT]
────────────────────────
```

of @base_prompt.txt by index 1. 2. 3. 4. ...

6. Put 5. prompt to llm api and get json
7. Add title, artist number, url to json which AI given

```json
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

8. Put data from 3, 7 to the database.

## Rogic 2 (Cover)

1. Put playlist to the code
2. Get video link in the playlist
3. Get metadata of video by Youtube v3 api
4. Check is the song is cover by find word on title such as [cover, 커버, ...]
5. Link to original song and put it in table.
6. Use channel name to get artist
7. Put the album_id and release_year to `NULL`

## Genre List

The number and genre which AI will use, and which going to put into the `genres` taㅗble
```
1 Hip-hop
2 R&B
3 Pop
4 Rock
5 Electronic
6 Jazz
7 Classical
8 Country
9 Metal
10 Folk
11 Reggae
12 Latin
13 K-pop
14 J-pop
15 Vocaloid
16 Soundtrack
17 Indie
18 Traditional
19 Blues
20 Funk
21 Soul
22 Gospel
23 Punk
24 Alternative
25 World
26 Afro
27 Experimental
28 Dance
29 Instrumental
30 Ambient
31 Ballad
100 Boom Bap
101 Trap
102 Drill
103 Conscious Rap
104 Jazz Rap
105 Experimental Hip-hop
106 Rage Rap
107 Cloud Rap
108 Gangsta Rap
109 Alternative Hip-hop
110 Lo-fi Hip-hop
111 Emo Rap
112 Hardcore Hip-hop
113 East Coast Rap
114 West Coast Rap
115 Southern Rap
116 Underground Rap
117 Pop Rap
118 Latin Trap
119 K-Hip-hop
120 UK Rap
121 French Rap
122 Detroit Rap
123 Memphis Rap
124 Phonk
125 Pluggnb
126 Hypertrap
127 Industrial Hip-hop
128 Horrorcore
129 Old School Rap
130 Contemporary R&B
131 Neo Soul
132 Alternative R&B
133 Smooth R&B
134 Quiet Storm
135 Funk R&B
136 Soul R&B
137 Trap Soul
138 K-R&B
139 UK R&B
140 Blue-eyed Soul
141 Retro Soul
142 Psychedelic Soul
143 Progressive R&B
144 Bedroom R&B
145 Gospel R&B
146 Urban R&B
147 Dance R&B
148 Indie R&B
149 Pop R&B
150 Dance Pop
151 Synth Pop
152 Electropop
153 Teen Pop
154 Art Pop
155 Indie Pop
156 Dream Pop
157 Chamber Pop
158 Baroque Pop
159 Power Pop
160 Pop Rock
161 K-Pop Dance
162 J-Pop Idol
163 Acoustic Pop
164 Tropical Pop
165 Latin Pop
166 Europop
167 Bubblegum Pop
168 Dark Pop
169 Alternative Pop
170 Alternative Rock
171 Indie Rock
172 Punk Rock
173 Classic Rock
174 Shoegaze
175 Post Rock
176 Hard Rock
177 Garage Rock
178 Grunge
179 Progressive Rock
180 Psychedelic Rock
181 Britpop
182 Math Rock
183 Folk Rock
184 Blues Rock
185 Glam Rock
186 Post Punk
187 Emo Rock
188 Gothic Rock
189 Stoner Rock
190 Noise Rock
191 Christian Rock
192 Surf Rock
193 Industrial Rock
194 Soft Rock
195 Symphonic Rock
196 Krautrock
197 Experimental Rock
198 Rap Rock
199 Pop Punk
200 House
201 Techno
202 Trance
203 Dubstep
204 Drum and Bass
205 Ambient
206 Synthwave
207 Vaporwave
208 Electro House
209 Deep House
210 Progressive House
211 Future Bass
212 Hardstyle
213 Psytrance
214 Minimal Techno
215 Acid House
216 Detroit Techno
217 UK Garage
218 Breakbeat
219 IDM
220 Glitch
221 Electro
222 Dancehall Electronic
223 Trap Electronic
224 Chillwave
225 Downtempo
226 Big Room
227 Bounce
228 Hardcore
229 Jungle
230 Eurodance
231 Tech House
232 Melodic Techno
233 Future House
234 Bass House
235 UK Bass
236 Lo-fi Electronic
237 Hyperpop
238 Electroclash
239 Trip Hop
240 Bebop
241 Swing
242 Smooth Jazz
243 Free Jazz
244 Fusion
245 Latin Jazz
246 Cool Jazz
247 Hard Bop
248 Jazz Funk
249 Acid Jazz
250 Modal Jazz
251 Avant-garde Jazz
252 Big Band
253 Contemporary Jazz
254 Vocal Jazz
255 Gypsy Jazz
256 Soul Jazz
257 Nu Jazz
258 Spiritual Jazz
259 Jazz Rap
260 Heavy Metal
261 Death Metal
262 Black Metal
263 Thrash Metal
264 Power Metal
265 Doom Metal
266 Metalcore
267 Post Metal
268 Symphonic Metal
269 Progressive Metal
270 Nu Metal
271 Folk Metal
272 Industrial Metal
273 Speed Metal
274 Groove Metal
275 Melodic Death Metal
276 Technical Death Metal
277 Sludge Metal
278 Alternative Metal
279 Glam Metal
280 Reggaeton
281 Bachata
282 Salsa
283 Latin Trap
284 Cumbia
285 Merengue
286 Latin Rock
287 Latin Pop
288 Regional Mexican
289 Bossa Nova
290 Samba
291 Flamenco Pop
292 Corrido
293 Tango Nuevo
294 Latin R&B
295 Brazilian Funk
296 Latin Jazz
297 Tropical
298 Urbano Latino
299 Mariachi Pop
1000 UK Drill
1001 Chicago Drill
1002 Brooklyn Drill
1003 Jersey Drill
1004 Bronx Drill
1005 Detroit Drill
1006 Korean Drill
1007 French Drill
1008 Dark Drill
1009 Melodic Drill
1010 Atlanta Trap
1011 Rage Trap
1012 Emo Trap
1013 Experimental Trap
1014 Latin Trap Wave
1015 Hyper Trap
1016 Trap Metal
1017 Pop Trap
1018 Industrial Trap
1019 Cloud Trap
1020 Deep Tech House
1021 Acid Techno
1022 Psytrance Goa
1023 Liquid Drum and Bass
1024 Neurofunk
1025 Chillstep
1026 Future Garage
1027 Hard Trance
1028 Euro Trance
1029 Minimal House
1030 Organic House
1031 Dark Techno
1032 Vaportrap
1033 Synthpop Retro
1034 Outrun Synthwave
1035 Dreamwave
1036 Lo-fi House
1037 Electro Swing
1038 Glitchcore
1039 Hypercore
1040 Blackgaze
1041 Midwest Emo
1042 Screamo Revival
1043 Post Hardcore
1044 Dreamgaze
1045 Space Rock
1046 Desert Rock
1047 Noise Pop
1048 Gothic Doom
1049 Indie Folk Rock
1050 City Pop
1051 K-Indie Pop
1052 Bedroom Pop
1053 Darkwave Pop
1054 Electro Ballad
1055 Viral Pop
1056 Idol Pop
1057 Future Pop
1058 Soft Pop Revival
1059 Acoustic Ballad
1060 Alt Neo Soul
1061 K-Alt R&B
1062 Indie Soul
1063 Future R&B
1064 Chill R&B
1065 Retro R&B
1066 Trap Soul Wave
1067 Psychedelic R&B
1068 Bedroom R&B Wave
1069 Jazz Soul
1070 Corrido Tumbado
1071 Baile Funk
1072 Latin Drill
1073 Neo Perreo
1074 Afro Latin
1075 Brazilian Phonk
1076 Latin House
1077 Tropical House Latin
1078 Salsa Romantica
1079 Modern Bachata
1080 Trot
1081 Gugak Fusion
1082 K-Ballad
1083 J-Rock Visual Kei
1084 Anime Opening Rock
1085 Vocaloid Electro
1086 Vocaloid Ballad
1087 J-Idol Pop
1088 K-Idol EDM
1089 K-Hip-hop Trap
1090 Acid Bop
1091 Spiritual Fusion
1092 Modern Big Band
1093 Lo-fi Jazz
1094 Jazztronica
1095 Chill Jazzhop
1096 Contemporary Swing
1097 Neo Bebop
1098 Avant Fusion
1099 Cinematic Jazz
1100 Blackened Death Metal
1101 Symphonic Black Metal
1102 Melodic Metalcore
1103 Djent
1104 Deathcore
1105 Progressive Death
1106 Doomgaze
1107 Industrial Black
1108 Power Symphonic
1109 Viking Metal
```

## DB Tree

```tree
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

| song_index | title | artist_id | group_id | album_id | release_year | url | original_song_id |
| - | - | - | - | - | - | - | - |
| 1 | Seven (feat. Latto) | 10 | 3 | 1 | 2023 | <https://music.youtube.com/watch?v=Vs64cZbeY88> | 1 |
| ... | .... | ... | ... | ... | ... | ... | ... |

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
