## Single Scene Image Lab Quality Checks

The Single Scene Image Lab is the safest place to inspect image quality from the Visual Prompt Engine before running full video production. It should be used for one scene at a time: prompt preview first, then at most one OpenAI image. Do not start voice, motion, timeline, or render steps from this quality check.

Recommended controls for documentary tests:
- `visual_preset`: `documentary_realism` for civic, economic, and human-interest scenes; `dark_mystery` for true-crime and mystery scenes.
- `prompt_detail_level`: `deep`.
- `provider_target`: `openai_image`.
- `text_safety_mode`: `strict_no_text`.
- `visual_consistency_mode`: `one_style_per_video`.

Current baseline topics:
- Economy: `Steigende Preise verunsichern Familien` with a family reviewing grocery costs at home.
- True Crime: `Eine Ermittlerin rekonstruiert den letzten Abend` with an investigator reviewing blank, unmarked evidence cards.
- Mystery: `Ein verlassenes Dorf in den Bergen sorgt fuer Fragen` with an empty mountain village street in fog.

Visual checks:
- The subject should be concrete and documentary-grounded, not the headline copied as a literal subject.
- The frame should have a clear focal point, foreground subject or texture, midground context, and a softly defocused background.
- Documents, receipts, notes, evidence cards, packages, and screens should be blank, unreadable, unbranded, or softly out of focus.
- People should look believable and restrained, not stock-photo posed or standing around without visual purpose.
- Overlay space should remain natural and usable without forcing empty white walls into every image.
- Lighting should feel grounded: soft directional natural light or believable practical light, without theatrical color casts.

Known risks:
- Fake writing can still appear on receipts, notes, evidence photos, packaging, labels, screens, or office props.
- Generic rooms can dilute the scene if the title or narration lacks concrete visual context.
- Stock-photo-like people can appear when the prompt asks for broad social themes without a focused moment.
- Too little overlay space can make later editorial titling harder, especially in crowded kitchens or offices.

Current good state:
- Prompt Preview returns structured Visual Prompt Anatomy, prompt quality score, risk flags, negative prompt, and the OpenAI Image formatted prompt.
- The Preview endpoint is covered for the three baseline topics and verifies text-artifact hardening through `strict_no_text`.
- Recent image-lab runs produced usable documentary stills for economy, true-crime, and mystery scenes without voice, motion, or render.
- The best results came from concrete visual moments: family at a table, investigator with blank cards, and empty village street depth.

Next recommendation:
- Keep using the Single Scene Image Lab for additional image samples before changing production flows.
- Compare 2-3 image samples per topic when judging visual quality; do not overfit the prompt anatomy to a single lucky or unlucky image.
- Only after the image baseline is stable should the team run full-video checks with voice, motion, and render.
