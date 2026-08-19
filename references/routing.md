# Input classification and visual routing

## Required intake

Resolve and record:

- brand, model, category, product name, and current workspace
- target platform and task profile
- verified product facts and unresolved facts
- requested image count, output ratios, screen count, and Screen 2 card count
- every input image, its source, and its role

Use `DETAIL_PAGE` when the user requests a detail page; otherwise select the matching profile from `task-profiles.md`. Do not guess a platform when it materially changes the plan; record `未明确` until confirmed or use a clearly labeled neutral baseline.

## Image roles

Assign one primary role to every image. Add secondary roles only when justified. Record `controls_routing` for each image, and record the user's normalized `style_direction` separately.

| Role | Meaning | Allowed use |
|---|---|---|
| `PRODUCT_SOURCE` | Current product photo, detail, packaging, or structural view | Product identity, visible facts, fidelity reference |
| `STYLE_BENCHMARK` | Mood, color, lighting, scene, or aesthetic reference | Extract visual language only; ignore its product facts |
| `LAYOUT_WIREFRAME` | Wireframe, sketch, completed layout used for composition | Extract hierarchy and placement only |
| `REDESIGN_SOURCE` | Existing finished artwork the user wants improved | Diagnose and preserve intentional strengths while correcting defects |

Never classify a competitor or inspiration product image as `PRODUCT_SOURCE` unless the user explicitly confirms it is the current product.

Only `PRODUCT_SOURCE` images may enter `product-identity-lock.json`. For each current-product image, record its view angle, visible features, occlusions, and whether it is suitable as a primary or auxiliary generation reference. A style benchmark can guide color, light, scene, or composition but can never replace an angle-matched product source.

## Visual mode router

Choose exactly one mode using this priority:

1. `REDESIGN_MODE`: a controlling `REDESIGN_SOURCE` exists because the user asks to improve, revise, remake, or diagnose it.
2. `STYLE_FUSION_MODE`: at least one controlling `STYLE_BENCHMARK` or `LAYOUT_WIREFRAME` exists and the request asks to follow, combine, benchmark, or borrow it.
3. `STYLE_GUIDED_MODE`: no image reference controls the result, but `style_direction` contains an explicit style, mood, era, material, color, or art direction.
4. `FREE_FISSION_MODE`: no controlling reference and no explicit style direction exists.

Record `visual_mode_reason`, controlling image IDs, extracted style vectors, and prohibited transfers.

## Mode behavior

- `REDESIGN_MODE`: diagnose hierarchy, readability, product prominence, lighting, composition, conversion logic, and platform fit. A/B may preserve the original visual DNA with substantive corrections; C must be a stronger reframing.
- `STYLE_FUSION_MODE`: extract the common denominator across all controlling references. Keep shared aesthetic genes while differentiating A/B/C through layout, scene, props, conversion emphasis, or visual temperature.
- `STYLE_GUIDED_MODE`: translate the user's words into a concrete color, light, material, scene, and composition vector. Do not invent a reference image.
- `FREE_FISSION_MODE`: make A/B/C substantially different in worldview, color temperature, scene language, and conversion emphasis. A simple background-color swap is invalid.

## Reference isolation

For every non-product reference, list:

- elements that may transfer: palette, lighting, texture, rhythm, composition, camera language
- elements that may not transfer: brand, model, materials, dimensions, structure, accessories, certifications, claims, text, price, service, or product-specific styling
