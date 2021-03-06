#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

##
# Counterpoint.py
# for reading in MIDI files and outputting their belief prop
# Forked from counterpoint.py by Anthony Theocharis on Github
# by Adam Krebs and Eric Hong, Winter 2011
##

from mingus.midi.MidiFileIn import MIDI_to_Composition
from mingus.midi.MidiFileOut import write_Composition
from mingus.containers import Note, NoteContainer, Bar, Composition, Instrument, Track
from mingus.extra.LilyPond import from_Composition, to_png, to_pdf
from structures import Soprano, Alto, Tenor, Bass, NoteNode, NoteList, create_note_lists
from rules import *
from errors import *
from belief import *
from species import first_species, second_species, third_species, fourth_species
import sys
from optparse import OptionParser

###
# WE'RE GOING TO MAKE A MAJOR ASSUMPTION IN THIS PROGRAM. WE WILL ASSUME THAT
# NO TRACK WILL HAVE POLYPHONY. ALL NOTES IN A TRACK WILL START ONLY AFTER
# THE PREVIOUS NOTE HAS FINISHED.
###

def setup_tracks(midi_file_out=None):
    from tracks import melodies, cantus_firmus, key, meter, species, author
    # Create a composition, and add the vocal tracks to it.
    composition = Composition()
    composition.set_title('Counterpoint Exercise', '')
    composition.set_author(author, '')

    # Set up our vocal 'tracks' with the notes, key, meter defined in tracks.py
    tracks = {}
    for voice in [Soprano, Alto, Tenor, Bass]:
        if len(melodies[voice.name]):
            tracks[voice.name] = Track(instrument=voice())
            tracks[voice.name].add_bar(Bar(key=key, meter=meter))
            tracks[voice.name].name = voice.name
            for note in melodies[voice.name]:
                tracks[voice.name].add_notes(*note)
            composition.add_track(tracks[voice.name])

    if midi_file_out is not None:
        # Save the midi file!
        write_Composition(midi_file_out, composition, verbose=True)

    return composition, [], species

def setup_midi(midi_file_in, fill_type):
    composition, bpm = MIDI_to_Composition(midi_file_in, fill_type)
    errors = []
    if len(composition.tracks) < 2 or len(composition.tracks) > 4 and fill_type is not "guess":
        errors.append('MIDI file must contain 2-4 tracks only.')
    for track in composition:
        if track.name not in ['Soprano', 'Alto', 'Tenor', 'Bass']:
            errors.append('Illegal track name "%": MIDI file tracks must be named one of: "Soprano", "Alto", "Tenor", or "Bass"' % track.name)
        else:
            for voice in [Soprano, Alto, Tenor, Bass]:
                if track.name == voice.name:
                    track.instrument = voice
    return composition, errors

def main():
    parser = OptionParser()
    parser.add_option('-t', action='store_true', dest='from_tracks', help='Read tracks from tracks.py. If encountered, will ignore instructions to read from MIDI file.')
    parser.add_option('-r', '--read-midi', dest='input_midi_file', help='Read tracks from midi provided MIDI_FILE. If encountered, will ignore instructions to write to MIDI file.', metavar='MIDI_FILE')
    # We're only using species 1    parser.add_option('-s', '--species', dest='species', help='One of 1, 2, or 4. Only applies to MIDI files.', metavar='SPECIES', type='int', default=1)
    parser.add_option('-w', '--write-midi', dest='output_midi_file', help='Write midi file OUTPUT_FILE', metavar='OUTPUT_FILE')
    parser.add_option('-p', '--write-png', dest='png_file', help='Write printed music to PNG_FILE', metavar='PNG_FILE')
    parser.add_option('-z', dest='typeset_midi_file', help="Testing option. Read in a midi file, but do not test it for errors. Can be used with -w, -p and -l", metavar='MIDI_FILE')
    parser.add_option('-l', dest='lilypond_file', help="Testing option. Write lilypond string to LY_FILE.", metavar="LY_FILE")
    parser.add_option('-g', '--guess', dest='guess', help='Guess the counterpoint for several missing notes')
    parser.add_option('-f', '--fill-in', dest='fill_in', help='Create new counterpoint composition based on the piece.', metavar="PIECE_TYPE")

    options, args = parser.parse_args()

    if options.typeset_midi_file:
        composition, bpm = MIDI_to_Composition(options.typeset_midi_file)
        if options.png_file:
            string = from_Composition(composition)
            to_png(string, options.png_file)
        if options.output_midi_file:
            write_Composition(options.output_midi_file, composition, verbose=True)
        if options.lilypond_file:
            string = from_Composition(composition)
            lf = open(options.lilypond_file, 'w')
            lf.write(string)
            lf.close()
        return


    errors = None
    composition = None
    species = options.species

    fill_type = "guess" ## for testing

    if options.from_tracks:
        # read the tracks from tracks.py
        composition, errors, species = setup_tracks(options.output_midi_file, fill_type)
    elif options.input_midi_file:
        # read the tracks from a midi file
        composition, errors = setup_midi(options.input_midi_file)

    if errors:
        print >> sys.stderr, '%s: ERROR(S) ENCOUNTERED WHEN READING MUSIC:' % sys.argv[0]
        print >> sys.stderr, '\n'.join(errors)
        sys.exit(1)
    elif composition is None:
        parser.error('Insufficient arguments provided. Use the -h argument to display help.')
        sys.exit(0)

    # Compute any errors.
    rulesets = [first_species, second_species, third_species, fourth_species]
    error_dict = rulesets[species-1](composition)

    # Convert the errors dict to a standard format
    errors = standardize_errors(error_dict)

    b = new belief(composition,"Bach",fill_type)
    b.train()
    b.test()


    if options.png_file:
        # Save the PNG
        string = from_Composition(composition)
        to_png(string, options.png_file)

    if options.lilypond_file:
        # save the Lilypond file
        string = from_Composition(composition)
        lf = open(options.lilypond_file, 'w')
        lf.write(string)
        lf.close()

if __name__ == "__main__":
    main()

