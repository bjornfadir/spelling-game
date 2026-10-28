import json
W=[("feet","I wear socks on my two feet.","Two feet, two e's."),
("deep","The water in the pool is very deep.","Two eyes look down into the deep water. Two e's."),
("sleep","At night I go to sleep in my bed.","Close your two eyes to sleep. Two e's."),
("week","There are seven days in a week.","Every week has two weekend days. Two e's."),
("bleed","If you cut your finger, it can bleed.","If you fall on your knee, it can bleed. Knee and bleed both have double e."),
("beak","A bird eats with its beak.","A bird eats with its beak. Eat and beak both have e, a."),
("east","The sun comes up in the east.","The sun is up early in the east. Early and east both start with e, a."),
("steam","Hot tea makes white steam.","Steam comes from hot tea. Tea and steam both have e, a."),
("seal","The seal swims and claps its flippers.","A seal lives in the sea. Sea and seal both have e, a."),
("peas","Green peas grow in a pod.","I eat my peas. Eat and peas both have e, a.")]
c={}
for w,s,t in W:
    c["w_"+w]=[w,0.8]; c["s_"+w]=[s,0.85]; c["t_"+w]=[t,0.85]
# Letter names: a capital letter plus a full stop reads as the letter's name on ElevenLabs.
# (Kokoro needed phonetic spellings like "bee"/"ef" instead.)
L="abdefklmpstw"
for k in L: c["l_"+k]=[k.upper()+".",0.85]
c["intro"]=['Listen to the long E sound! <break time="0.3s" /> Eee! <break time="0.4s" /> Like in: me, <break time="0.25s" /> see, <break time="0.25s" /> and tree!',1.0]
for k,v in {"p0":"Great job!","p1":"Super!","p2":"You got it!","p3":"Brilliant!","perfect":"Perfect!","almost":"Almost! Look carefully.","done10":"Perfect score! Well done!"}.items(): c[k]=[v,0.9]
nums=["zero","one","two","three","four","five","six","seven","eight","nine"]
for i,n in enumerate(nums): c[f"score{i}"]=[f"You got {n} out of ten. Well done!",0.9]
# Pronunciation layer: every spoken line passes through SAY before it reaches the TTS engine.
# The game shows its own text (WORDS in src/game.html), so respellings here change only the audio.
# Add an entry whenever a clip comes out wrong; prefer respelling just the problem bit (a sound,
# a letter name, a tricky word) over the whole line, because respelled ordinary words
# ("peez" for peas) often sound worse. ElevenLabs <break time="0.3s" /> tags are allowed for pauses.
SAY={
  "e, a":"E, A",        # letter names, not the sounds "eh, ah"
  "two e's":"two E's",
  "double e":"double E",
}
for k,(t,sp) in c.items():
    for a,b in SAY.items(): t=t.replace(a,b)
    c[k]=[t,sp]
json.dump(c,open("clips.json","w"),indent=0); print(len(c),"clips")
