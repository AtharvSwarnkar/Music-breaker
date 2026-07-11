import torch
from app.models.clap_model import clap_model


class InstrumentDetector:

    def __init__(self):

        self.model = clap_model.model
        self.processor = clap_model.processor
        self.device = clap_model.device

        """
CLAP instrument prompt bank.
 
Structure: each instrument has exactly 12 prompts, grouped into 4 categories
(3 prompts each). The category comments are for maintainability only —
the underlying value is still a flat list of 12 strings per instrument,
so it's a drop-in replacement for the existing self.instrument_prompts dict.
 
Categories:
    1. Identity          - bare statement of what the instrument is
    2. Timbre & Tone      - what it sounds like (not what someone does)
    3. Playing Technique  - how it's being played, instrument stays the subject
    4. Musical Context    - production vocabulary + musical role + genre
 
Usage notes:
    - No "a person playing..." phrasing anywhere; the instrument is always
      the grammatical subject, matching caption-style data CLAP was trained on.
    - Genre/technique words are deliberately varied within each instrument
      (rock/funk/jazz/blues/country/ambient/etc.) instead of repeating
      near-synonyms like "distorted/overdriven/fuzzy/high-gain" back to back.
    - Recommended usage: average the text embeddings of all 12 prompts
      (or all 3 within a category) into a single class centroid before
      comparing against the audio embedding, rather than taking the
      single best-matching prompt.
"""
 
        # self.instrument_prompts = {
        
        #     "electric_guitar": [
        #         # Identity
        #         "The sound of an electric guitar.",
        #         "An amplified electric guitar.",
        #         "An electric guitar playing musical notes.",
        #         # Timbre & Tone
        #         "A distorted electric guitar with a high-gain rock tone.",
        #         "A clean funk electric guitar with a bright, percussive tone.",
        #         "A hollow-body jazz electric guitar with a warm, mellow tone.",
        #         # Playing Technique
        #         "Palm-muted electric guitar rhythm chugging.",
        #         "Electric guitar power chords with heavy distortion.",
        #         "A blues electric guitar solo bending strings with vibrato.",
        #         # Musical Context
        #         "Electric guitar layered with bass and drums in a rock mix.",
        #         "Country electric guitar accompanying a lead vocalist.",
        #         "Ambient electric guitar with delay and reverb in a studio production.",
        #     ],
        
        #     "acoustic_guitar": [
        #         # Identity
        #         "The sound of an acoustic guitar.",
        #         "A steel-string acoustic guitar.",
        #         "An acoustic guitar playing musical notes.",
        #         # Timbre & Tone
        #         "A warm, resonant acoustic guitar with natural string tone.",
        #         "A bright, jangly acoustic guitar with steel strings.",
        #         "A mellow nylon-string acoustic guitar with a soft tone.",
        #         # Playing Technique
        #         "Fingerstyle acoustic guitar picking a melodic pattern.",
        #         "Acoustic guitar strumming open chords.",
        #         "A capoed acoustic guitar with bright fingerpicked arpeggios.",
        #         # Musical Context
        #         "Close-mic acoustic guitar in a studio recording.",
        #         "Acoustic guitar accompanying a folk singer's vocal melody.",
        #         "Acoustic guitar layered with light percussion in an indie pop production.",
        #     ],
        
        #     "bass_guitar": [
        #         # Identity
        #         "The sound of an electric bass guitar.",
        #         "A low-frequency bass guitar.",
        #         "A bass guitar playing musical notes.",
        #         # Timbre & Tone
        #         "A deep, round electric bass guitar tone.",
        #         "A bright, punchy bass guitar with a clicky attack.",
        #         "A smooth fretless bass guitar with a sliding tone.",
        #         # Playing Technique
        #         "Fingerstyle electric bass guitar groove.",
        #         "Slap bass guitar with percussive pops and snaps.",
        #         "A picked bass guitar line with syncopated rhythm.",
        #         # Musical Context
        #         "Bass guitar providing the low-end foundation of a rock mix.",
        #         "Bass guitar locking in with the kick drum in a funk groove.",
        #         "Bass guitar layered beneath guitars and drums in a studio recording.",
        #     ],
        
        #     "drum_kit": [
        #         # Identity
        #         "The sound of a drum kit.",
        #         "An acoustic drum set.",
        #         "A drum kit playing a rhythmic pattern.",
        #         # Timbre & Tone
        #         "A punchy drum kit with a tight snare and deep kick.",
        #         "A bright drum kit with crisp cymbals and hi-hat.",
        #         "A roomy drum kit with natural ambience and resonance.",
        #         # Playing Technique
        #         "A drum kit groove with steady kick and snare backbeat.",
        #         "A drum fill with rapid tom rolls into a cymbal crash.",
        #         "Brushed snare and ride cymbal in a jazz drum pattern.",
        #         # Musical Context
        #         "Drum kit driving the groove in a rock rhythm section.",
        #         "Close-mic drum kit with compression in a studio recording.",
        #         "Drum kit layered with bass and rhythm guitar in a pop production.",
        #     ],
        
        #     "piano": [
        #         # Identity
        #         "The sound of a piano.",
        #         "An acoustic grand piano.",
        #         "A piano playing musical notes.",
        #         # Timbre & Tone
        #         "A bright grand piano with a resonant, hammered tone.",
        #         "A soft upright piano with a warm, muted tone.",
        #         "A rich piano tone with sustained pedal resonance.",
        #         # Playing Technique
        #         "A piano playing arpeggiated chords across the keyboard.",
        #         "Percussive piano chords struck with rhythmic emphasis.",
        #         "A piano melody played with expressive dynamics and rubato.",
        #         # Musical Context
        #         "Piano accompanying a singer's lead vocal melody.",
        #         "Piano layered with strings in an orchestral film score.",
        #         "A close-mic piano recording in a studio session.",
        #     ],
        
        #     "synthesizer": [
        #         # Identity
        #         "The sound of a synthesizer.",
        #         "An electronic synthesizer.",
        #         "A synthesizer playing musical notes.",
        #         # Timbre & Tone
        #         "A bright, filtered synthesizer lead tone.",
        #         "A smooth, sustained synthesizer pad texture.",
        #         "A buzzing analog synthesizer bass tone.",
        #         # Playing Technique
        #         "A synthesizer playing a plucky, percussive arpeggio.",
        #         "A synthesizer sustaining a slow, evolving pad.",
        #         "A synthesizer lead bending pitch with portamento.",
        #         # Musical Context
        #         "A synthesizer layered with drums in an electronic dance production.",
        #         "Synthesizer pad accompanying a vocalist in a pop ballad.",
        #         "A synthesizer bass locked in with a drum machine in a studio mix.",
        #     ],
        
        #     "violin": [
        #         # Identity
        #         "The sound of a violin.",
        #         "A solo violin.",
        #         "A violin playing musical notes.",
        #         # Timbre & Tone
        #         "A bright, singing violin tone in its upper register.",
        #         "A warm violin tone with expressive vibrato.",
        #         "A thin, nasal violin tone with a sustained bow stroke.",
        #         # Playing Technique
        #         "A violin played pizzicato with plucked staccato notes.",
        #         "A violin bowed with long, sustained legato phrases.",
        #         "A fast, rhythmic fiddle tune with rapid bowing.",
        #         # Musical Context
        #         "A violin section layered in an orchestral string arrangement.",
        #         "Solo violin accompanying a piano in a chamber recording.",
        #         "A folk violin layered with acoustic guitar in a studio mix.",
        #     ],
        
        #     "cello": [
        #         # Identity
        #         "The sound of a cello.",
        #         "A solo cello.",
        #         "A cello playing musical notes.",
        #         # Timbre & Tone
        #         "A deep, warm cello tone in its low register.",
        #         "A rich, resonant cello tone with expressive vibrato.",
        #         "A dark, mellow cello tone with a rounded edge.",
        #         # Playing Technique
        #         "A cello played pizzicato with plucked low notes.",
        #         "A cello bowed with long, sustained legato phrases.",
        #         "A cello playing a fast, rhythmic bowed passage.",
        #         # Musical Context
        #         "A cello section layered in an orchestral string arrangement.",
        #         "Solo cello accompanying a piano in a chamber recording.",
        #         "A cello layered beneath violins in a film score production.",
        #     ],
        
        #     "flute": [
        #         # Identity
        #         "The sound of a flute.",
        #         "A concert flute.",
        #         "A flute playing musical notes.",
        #         # Timbre & Tone
        #         "A bright, airy flute tone with a breathy edge.",
        #         "A warm, mellow flute tone in its low register.",
        #         "A clear, piercing flute tone in its high register.",
        #         # Playing Technique
        #         "A flute playing fast, fluttering staccato notes.",
        #         "A flute sustaining a smooth legato melodic phrase.",
        #         "A flute trilling rapidly between two adjacent notes.",
        #         # Musical Context
        #         "A flute melody layered over a string orchestra.",
        #         "Flute accompanying a vocalist in a folk arrangement.",
        #         "A close-mic flute recording in a chamber studio session.",
        #     ],
        
        #     "clarinet": [
        #         # Identity
        #         "The sound of a clarinet.",
        #         "A solo clarinet.",
        #         "A clarinet playing musical notes.",
        #         # Timbre & Tone
        #         "A warm, woody clarinet tone in its middle register.",
        #         "A dark, mellow clarinet tone in its low chalumeau register.",
        #         "A bright, reedy clarinet tone in its high register.",
        #         # Playing Technique
        #         "A clarinet playing fast, fluid runs.",
        #         "A clarinet sustaining a smooth legato phrase.",
        #         "A jazz clarinet with syncopated, bending phrasing.",
        #         # Musical Context
        #         "A clarinet melody layered over a klezmer ensemble.",
        #         "Clarinet accompanying a big-band woodwind section.",
        #         "A close-mic clarinet recording in a chamber studio.",
        #     ],
        
        #     "saxophone": [
        #         # Identity
        #         "The sound of a saxophone.",
        #         "An alto saxophone.",
        #         "A saxophone playing musical notes.",
        #         # Timbre & Tone
        #         "A warm, reedy saxophone tone with a smooth vibrato.",
        #         "A bright, buzzing saxophone tone with a sharp edge.",
        #         "A deep, growling baritone saxophone tone.",
        #         # Playing Technique
        #         "A saxophone honking staccato notes in a funk rhythm.",
        #         "A saxophone sustaining a smooth, soulful legato phrase.",
        #         "A saxophone solo with fast, syncopated jazz phrasing.",
        #         # Musical Context
        #         "A saxophone solo layered over a jazz rhythm section.",
        #         "Saxophone accompanying a vocalist in an R&B production.",
        #         "A close-mic saxophone recording with room ambience in a studio.",
        #     ],
        
        #     "trumpet": [
        #         # Identity
        #         "The sound of a trumpet.",
        #         "A brass trumpet.",
        #         "A trumpet playing musical notes.",
        #         # Timbre & Tone
        #         "A bright, brassy trumpet tone with a sharp edge.",
        #         "A soft, muted trumpet tone with a nasal quality.",
        #         "A warm trumpet tone with a rounded, mellow character.",
        #         # Playing Technique
        #         "A trumpet playing punchy staccato brass stabs.",
        #         "A trumpet sustaining a bold, held high note.",
        #         "A jazz trumpet solo with fast, syncopated phrasing.",
        #         # Musical Context
        #         "A trumpet section layered in a big-band brass arrangement.",
        #         "Trumpet accompanying a vocalist in a Latin jazz production.",
        #         "A close-mic trumpet recording with studio compression.",
        #     ],
        
        #     "trombone": [
        #         # Identity
        #         "The sound of a trombone.",
        #         "A slide trombone.",
        #         "A trombone playing musical notes.",
        #         # Timbre & Tone
        #         "A warm, buzzing trombone tone in its mid register.",
        #         "A deep, growling trombone tone in its low register.",
        #         "A bright brass trombone tone with a bold edge.",
        #         # Playing Technique
        #         "A trombone playing smooth glissando slides between notes.",
        #         "A trombone sustaining a low, held brass note.",
        #         "A muted trombone with a soft, wah-like phrase.",
        #         # Musical Context
        #         "A trombone section layered in a big-band horn arrangement.",
        #         "Trombone accompanying a brass ensemble in a ska production.",
        #         "A close-mic trombone recording with natural room ambience.",
        #     ],
        
        #     "organ": [
        #         # Identity
        #         "The sound of an organ.",
        #         "A pipe organ.",
        #         "An organ playing musical notes.",
        #         # Timbre & Tone
        #         "A rich, sustained organ tone with a droning harmonic texture.",
        #         "A warm Hammond organ tone with a swirling rotary effect.",
        #         "A deep, resonant pipe organ tone in its low register.",
        #         # Playing Technique
        #         "An organ sustaining long, held chords.",
        #         "A Hammond organ playing swelling, percussive chords.",
        #         "An organ playing deep, resonant bass pedal notes.",
        #         # Musical Context
        #         "A gospel organ layered with a choir in a church recording.",
        #         "Organ accompanying a rock band with a swirling rotary tone.",
        #         "A pipe organ layered in a cathedral studio recording with reverb.",
        #     ],
        
        #     "ukulele": [
        #         # Identity
        #         "The sound of a ukulele.",
        #         "A small four-string ukulele.",
        #         "A ukulele playing musical notes.",
        #         # Timbre & Tone
        #         "A bright, cheerful ukulele tone with a compact nylon-string sound.",
        #         "A warm, plucky ukulele tone with a light decay.",
        #         "A soft, mellow ukulele tone in its low register.",
        #         # Playing Technique
        #         "A ukulele strumming bright, rhythmic chords.",
        #         "A ukulele fingerpicking a soft island-style melody.",
        #         "A ukulele played with a percussive strumming pattern.",
        #         # Musical Context
        #         "A ukulele layered with light percussion in a tropical pop production.",
        #         "Ukulele accompanying a vocalist in an acoustic folk recording.",
        #         "A close-mic ukulele in a warm studio session.",
        #     ],
        
        #     "harmonica": [
        #         # Identity
        #         "The sound of a harmonica.",
        #         "A diatonic harmonica.",
        #         "A harmonica playing musical notes.",
        #         # Timbre & Tone
        #         "A breathy, reedy harmonica tone with a bending pitch.",
        #         "A raspy, overdriven harmonica tone with a bluesy edge.",
        #         "A warm, mellow harmonica tone with soft vibrato.",
        #         # Playing Technique
        #         "A harmonica bending notes in a bluesy phrase.",
        #         "A harmonica playing a fast, rhythmic riff.",
        #         "A harmonica sustaining a wailing, vibrato-laden note.",
        #         # Musical Context
        #         "A harmonica layered with acoustic guitar in a blues recording.",
        #         "Harmonica accompanying a vocalist in a folk production.",
        #         "A close-mic harmonica recording with natural room ambience.",
        #     ],
        
        #     "male_vocals": [
        #         # Identity
        #         "The sound of a male vocal.",
        #         "A male singing voice.",
        #         "A male vocal performing a melody.",
        #         # Timbre & Tone
        #         "A deep, warm male vocal tone.",
        #         "A bright, clear male vocal tone with sustained pitch.",
        #         "A raspy, soulful male vocal tone with vibrato.",
        #         # Vocal Technique
        #         "A male vocal sustaining a held note with vibrato.",
        #         "A male vocal delivering a rhythmic, syncopated verse.",
        #         "A male vocal belting a powerful high note.",
        #         # Musical Context
        #         "A male lead vocal layered over a band mix.",
        #         "Male vocal harmonies layered in a studio recording.",
        #         "A close-mic male vocal with reverb in a pop production.",
        #     ],
        
        #     "female_vocals": [
        #         # Identity
        #         "The sound of a female vocal.",
        #         "A female singing voice.",
        #         "A female vocal performing a melody.",
        #         # Timbre & Tone
        #         "A bright, clear female vocal tone with sustained pitch.",
        #         "A warm, soulful female vocal tone with vibrato.",
        #         "A breathy, airy female vocal tone in a soft passage.",
        #         # Vocal Technique
        #         "A female vocal sustaining a held note with vibrato.",
        #         "A female vocal delivering a rhythmic, syncopated verse.",
        #         "A female vocal belting a powerful high note.",
        #         # Musical Context
        #         "A female lead vocal layered over a band mix.",
        #         "Female vocal harmonies layered in a studio recording.",
        #         "A close-mic female vocal with reverb in a pop production.",
        #     ],
        # }

        self.instrument_prompts = {
 
    #  Guitar
    "guitar": [
        # Identity
        "The sound of a guitar.",
        "A steel-string or electric guitar.",
        "A guitar playing musical notes.",
        # Timbre & Tone
        "A distorted electric guitar with a driving rock tone.",
        "A warm acoustic guitar with a natural resonant tone.",
        "A clean, bright guitar tone with chiming overtones.",
        # Playing Technique
        "A guitar strumming rhythmic chords.",
        "A guitar fingerpicking a melodic pattern.",
        "A guitar solo with bent notes and sustained vibrato.",
        # Musical Context
        "Guitar layered with bass and drums in a band mix.",
        "Guitar accompanying a lead vocalist.",
        "A guitar riff driving a rock or pop production.",
    ],
 
    # 🥁 Drums & Percussion
    "drums_percussion": [
        # Identity
        "The sound of a drum kit.",
        "A set of percussion instruments.",
        "Drums and percussion playing a rhythmic pattern.",
        # Timbre & Tone
        "A punchy drum kit with a tight snare and deep kick.",
        "A warm, resonant hand percussion tone from congas and bongos.",
        "A bright drum kit with crisp cymbals and hi-hat.",
        # Playing Technique
        "A drum kit groove with a steady kick and snare backbeat.",
        "Hand percussion played with open and muted strikes.",
        "A drum fill with rapid tom rolls into a cymbal crash.",
        # Musical Context
        "Drums and percussion driving the groove in a rhythm section.",
        "A drum kit layered with bass in a studio recording.",
        "Percussion layered with a full band in an Afrobeat or Latin production.",
    ],
 
    # 🎹 Piano & Keyboard
    "piano_keyboard": [
        # Identity
        "The sound of a piano.",
        "An acoustic or electric keyboard.",
        "A piano playing musical notes.",
        # Timbre & Tone
        "A bright grand piano with a resonant, hammered tone.",
        "A warm electric piano tone with a bell-like character.",
        "A rich organ tone with a sustained harmonic texture.",
        # Playing Technique
        "A piano playing arpeggiated chords across the keyboard.",
        "A keyboard comping rhythmic jazz chords.",
        "An organ sustaining long, held chords.",
        # Musical Context
        "Piano accompanying a singer's lead vocal melody.",
        "Keyboard layered with bass and drums in a soul production.",
        "A close-mic piano recording in a studio session.",
    ],
 
    # 🎻 Strings
    "strings": [
        # Identity
        "The sound of an orchestral string instrument.",
        "A bowed string instrument such as a violin or cello.",
        "Strings playing musical notes.",
        # Timbre & Tone
        "A bright, singing violin tone in its upper register.",
        "A deep, warm cello tone in its low register.",
        "A rich string section tone with layered harmonics.",
        # Playing Technique
        "A string instrument played pizzicato with plucked notes.",
        "Strings bowed with long, sustained legato phrases.",
        "A string section playing a fast, rhythmic bowed passage.",
        # Musical Context
        "A string section layered in an orchestral arrangement.",
        "Strings accompanying a vocalist in a ballad production.",
        "A string quartet layered in a chamber music recording.",
    ],
 
    # 🎺 Brass
    "brass": [
        # Identity
        "The sound of a brass instrument.",
        "A trumpet or trombone.",
        "Brass playing musical notes.",
        # Timbre & Tone
        "A bright, brassy trumpet tone with a sharp edge.",
        "A warm, buzzing trombone tone in its mid register.",
        "A bold brass section tone with layered harmonics.",
        # Playing Technique
        "A brass instrument playing punchy staccato stabs.",
        "A trombone sliding smoothly between notes.",
        "A brass section sustaining a bold harmonized chord.",
        # Musical Context
        "A brass section layered in a big-band arrangement.",
        "Brass accompanying a vocalist in a soul or funk production.",
        "A close-mic brass recording with studio compression.",
    ],
 
    # 🪈 Woodwinds
    "woodwinds": [
        # Identity
        "The sound of a woodwind instrument.",
        "A flute, clarinet, or saxophone.",
        "A woodwind playing musical notes.",
        # Timbre & Tone
        "A bright, airy flute tone with a breathy edge.",
        "A warm, reedy saxophone tone with a smooth vibrato.",
        "A woody clarinet tone in its middle register.",
        # Playing Technique
        "A woodwind sustaining a smooth legato melodic phrase.",
        "A saxophone honking staccato notes in a funk rhythm.",
        "A flute playing fast, fluttering staccato notes.",
        # Musical Context
        "A woodwind melody layered over a string orchestra.",
        "Saxophone accompanying a vocalist in an R&B production.",
        "A close-mic woodwind recording in a jazz studio session.",
    ],
 
    # 🎸 Bass
    "bass": [
        # Identity
        "The sound of an electric bass guitar.",
        "A low-frequency bass instrument.",
        "A bass guitar playing musical notes.",
        # Timbre & Tone
        "A deep, round electric bass guitar tone.",
        "A bright, punchy bass guitar with a clicky attack.",
        "A smooth fretless bass guitar with a sliding tone.",
        # Playing Technique
        "Fingerstyle electric bass guitar groove.",
        "Slap bass guitar with percussive pops and snaps.",
        "A picked bass guitar line with syncopated rhythm.",
        # Musical Context
        "Bass guitar providing the low-end foundation of a rock mix.",
        "Bass guitar locking in with the kick drum in a funk groove.",
        "Bass guitar layered beneath guitars and drums in a studio recording.",
    ],
 
    # 🎤 Vocals
    "vocals": [
        # Identity
        "The sound of a singing voice.",
        "A male or female vocal.",
        "A vocal performing a melody.",
        # Timbre & Tone
        "A deep, warm male vocal tone.",
        "A bright, clear female vocal tone with sustained pitch.",
        "A soulful vocal tone with expressive vibrato.",
        # Vocal Technique
        "A vocal sustaining a held note with vibrato.",
        "A vocal delivering a rhythmic, syncopated verse.",
        "A vocal belting a powerful high note.",
        # Musical Context
        "A lead vocal layered over a full band mix.",
        "Vocal harmonies layered in a studio recording.",
        "A close-mic vocal with reverb in a pop production.",
    ],
 
    # 🎼 Traditional / Folk
    "traditional_folk": [
        # Identity
        "The sound of a traditional folk instrument.",
        "A banjo, mandolin, or ukulele.",
        "A folk instrument playing musical notes.",
        # Timbre & Tone
        "A bright, twangy banjo tone with a metallic edge.",
        "A warm, plucky ukulele tone with a light decay.",
        "A reedy, breathy harmonica tone with a bending pitch.",
        # Playing Technique
        "A banjo playing a fast, rolling bluegrass pattern.",
        "A ukulele strumming bright, rhythmic chords.",
        "A harmonica bending notes in a bluesy phrase.",
        # Musical Context
        "A folk instrument layered with acoustic guitar in a bluegrass ensemble.",
        "Traditional folk instruments accompanying a vocalist in a country production.",
        "A close-mic folk instrument recording in an acoustic studio session.",
    ],
 
    # 🎛️ Synth
    "synth": [
        # Identity
        "The sound of a synthesizer.",
        "An electronic synth instrument.",
        "A synthesizer playing musical notes.",
        # Timbre & Tone
        "A bright, filtered synthesizer lead tone.",
        "A smooth, sustained synthesizer pad texture.",
        "A buzzing analog synthesizer bass tone.",
        # Playing Technique
        "A synthesizer playing a plucky, percussive arpeggio.",
        "A synthesizer sustaining a slow, evolving pad.",
        "A synthesizer lead bending pitch with portamento.",
        # Musical Context
        "A synthesizer layered with drums in an electronic dance production.",
        "Synthesizer pad accompanying a vocalist in a pop ballad.",
        "A synthesizer bass locked in with a drum machine in a studio mix.",
    ],
}
        self.all_prompts = []
        self.prompt_mapping = []

        for instrument, prompts in self.instrument_prompts.items():

            for prompt in prompts:

                self.all_prompts.append(prompt)
                self.prompt_mapping.append(instrument)

    def detect(self, audio):

        inputs = self.processor(
            text=self.all_prompts,
            audios=audio,
            sampling_rate=48000,
            return_tensors="pt",
            padding=True
        )

        inputs = {
            k: v.to(self.device)
            for k, v in inputs.items()
        }

        with torch.inference_mode():

            outputs = self.model(**inputs)

            similarity = torch.matmul(
                outputs.audio_embeds,
                outputs.text_embeds.T
            )

        similarity = similarity.squeeze().cpu().numpy()

        grouped_scores = {
            instrument: []
            for instrument in self.instrument_prompts.keys()
        }

        for instrument, score in zip(self.prompt_mapping, similarity):
            grouped_scores[instrument].append(float(score))

        scores = {}

        for instrument, values in grouped_scores.items():
            scores[instrument] = sum(values) / len(values)

        return scores
    

    def detect_batch(self, windows):

        inputs = self.processor(
            text=self.all_prompts,
            audios=windows,
            sampling_rate=48000,
            return_tensors="pt",
            padding=True
        )

        inputs = {
            k: v.to(self.device)
            for k, v in inputs.items()
        }

        with torch.inference_mode():

            outputs = self.model(**inputs)

            similarity = torch.matmul(
                outputs.audio_embeds,
                outputs.text_embeds.T
            )

        similarity = similarity.cpu().numpy()

        results = []

        for window_similarity in similarity:

            grouped_scores = {
                instrument: []
                for instrument in self.instrument_prompts.keys()
            }

            for instrument, score in zip(
                self.prompt_mapping,
                window_similarity
            ):
                grouped_scores[instrument].append(float(score))

            scores = {}

            for instrument, values in grouped_scores.items():
                scores[instrument] = sum(values) / len(values)

            results.append(scores)

        return results
    



    # def detect(self, audio):

    #     all_prompts = []
    #     prompt_mapping = []

    #     for instrument, prompts in self.instrument_prompts.items():

    #         for prompt in prompts:

    #             all_prompts.append(prompt)
    #             prompt_mapping.append(instrument)

    #     inputs = self.processor(
    #         text=all_prompts,
    #         audios=audio,
    #         sampling_rate=48000,
    #         return_tensors="pt",
    #         padding=True
    #     )

    #     inputs = {
    #         k: v.to(self.device)
    #         for k, v in inputs.items()
    #     }

    #     with torch.no_grad():

    #         outputs = self.model(**inputs)

    #         similarity = torch.matmul(
    #             outputs.audio_embeds,
    #             outputs.text_embeds.T
    #         )

    #     similarity = similarity.squeeze().cpu().numpy()

    #     grouped_scores = {}

    #     for instrument in self.instrument_prompts.keys():
    #         grouped_scores[instrument] = []

    #     for instrument, score in zip(prompt_mapping, similarity):
    #         grouped_scores[instrument].append(float(score))

    #     scores = {}

    #     for instrument, values in grouped_scores.items():
    #         scores[instrument] = sum(values) / len(values)

    #     return scores