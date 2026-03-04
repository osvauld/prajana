open Proof_graph

let swara_to_pitch (k : proof_graph) (octave : int) (swara : string) : string =
  let map = Setu.read_shabda k "swara-to-strudel" in
  let key = String.lowercase_ascii swara in
  let letter = match List.assoc_opt key map with
    | Some l -> l
    | None -> swara
  in
  if String.length letter = 1 && letter.[0] >= 'a' && letter.[0] <= 'g' then
    Printf.sprintf "%s%d" letter octave
  else
    letter

let compose_music (k : proof_graph) (seeds : string list) (walk : string list) (input : string) : unit =
  let has n = List.mem n seeds || List.mem n walk in
  let ornament_map = Setu.read_shabda k "ornament-to-strudel" in
  let strudel_map  = Setu.read_shabda k "strudel" in
  let orn key = Setu.shabda_get ornament_map key in
  let str key = Setu.shabda_get strudel_map key in

  Printf.printf "// strudel — stack of layers from proof graph\n";
  Printf.printf "// thaalam (avrti) | swara (matrika) | laya (velocity)\n\n";

  let octave = 3 in
  let input_tokens = if String.length input > 0
    then String.split_on_char ' ' (String.trim input)
    else ["shadja"; "gandhara"; "panchama"] in
  let pitches = List.map (swara_to_pitch k octave) input_tokens in

  let melody_pitches =
    if has "arohana" && has "avarohana" then pitches @ List.rev pitches
    else if has "avarohana" && not (has "arohana") then List.rev pitches
    else pitches
  in

  let vadi_bass =
    let mid = List.nth input_tokens (List.length input_tokens / 2) in
    swara_to_pitch k (octave - 1) mid
  in

  let vriddhi = orn "vriddhi" in
  let melody_pattern =
    let n = List.length melody_pitches in
    List.mapi (fun i p ->
      if has "nyasa" && i = n - 1 then
        (match vriddhi with Some v -> p ^ "*" ^ v | None -> p)
      else if has "kan-swara" && i > 0 then
        Printf.sprintf "<%s %s>" (List.nth melody_pitches (i-1)) p
      else p
    ) melody_pitches
    |> String.concat " "
  in

  let tivra = orn "tivra" in
  let laya_mod =
    if has "vriddhi-laya" then (match tivra with Some t -> ".fast(" ^ t ^ ")" | None -> "")
    else if has "kshaya-laya" then (match tivra with Some t -> ".slow(" ^ t ^ ")" | None -> "")
    else "" in

  let gain_val =
    if has "vriddhi-laya" then "0.9"
    else if has "kshaya-laya" then "0.5"
    else "0.8" in

  let spanda = orn "spanda" in
  let laghu  = orn "laghu" in
  let manda  = orn "manda" in
  let gamaka_add =
    if has "gamaka" && has "andolan" then
      (match spanda, laghu, manda with
      | Some s, Some l, Some m ->
        Printf.sprintf ".add(%s.range(0, %s)).add(%s.slow(%s).range(0, %s))"
          s l s m (string_of_float (float_of_string l /. 2.0))
      | _ -> "")
    else if has "gamaka" then
      (match spanda, laghu with
      | Some s, Some l -> Printf.sprintf ".add(%s.range(0, %s))" s l
      | _ -> "")
    else if has "andolan" then
      (match spanda, manda, laghu with
      | Some s, Some m, Some l -> Printf.sprintf ".add(%s.slow(%s).range(0, %s))" s m l
      | _ -> "")
    else "" in

  let gati  = orn "gati" in
  let purna = orn "purna" in
  let meend_mod =
    if has "meend" then
      (match gati, purna with
       | Some g, Some p -> Printf.sprintf ".%s(%s)" g p
       | _ -> "")
    else "" in

  let thaalam_beats = if has "akshara" then str "akshara" else str "thaalam" in
  let vadi_synth   = str "vadi" in
  let melody_synth = str "melody" in

  Printf.printf "stack(\n";

  (match thaalam_beats with
  | Some beats ->
    Printf.printf "  // thaalam -> avrti (the returning beat)\n";
    Printf.printf "  s(\"%s\").gain(0.4),\n\n" beats
  | None -> ());

  if has "vadi-swara" then begin
    Printf.printf "  // vadi-swara -> active-site (dominant drone)\n";
    Printf.printf "  note(\"%s\")" vadi_bass;
    (match vadi_synth with Some s -> Printf.printf ".sound(\"%s\")" s | None -> ());
    if laya_mod <> "" then Printf.printf "%s" laya_mod;
    Printf.printf ".gain(0.5).slow(2),\n\n"
  end;

  Printf.printf "  // swara -> matrika | arohana -> sequence -> gati\n";
  Printf.printf "  note(\"%s\")%s\n" melody_pattern gamaka_add;
  (match melody_synth with
  | Some s -> Printf.printf "    .sound(\"%s\")\n" s
  | None -> ());
  if meend_mod <> "" then Printf.printf "    %s\n" meend_mod;
  if laya_mod  <> "" then Printf.printf "    %s\n" laya_mod;
  Printf.printf "    .gain(%s)\n" gain_val;

  Printf.printf ")\n\n";

  Printf.printf "// graph chain:\n";
  Printf.printf "// thaalam -> avrti -> rhythm layer\n";
  if has "vadi-swara" then Printf.printf "// vadi-swara -> active-site -> bass drone\n";
  Printf.printf "// swara -> matrika -> melody\n";
  if has "arohana" then Printf.printf "// arohana -> sequence -> ascending\n";
  if has "avarohana" then Printf.printf "// avarohana -> sequence -> descending\n";
  if has "gamaka" then (match spanda with
    | Some s -> Printf.printf "// gamaka -> spanda (%s) -> sine on pitch\n" s
    | None -> ());
  if has "andolan" then (match spanda with
    | Some s -> Printf.printf "// andolan -> manda-spanda -> slow %s\n" s
    | None -> ());
  if has "meend" then (match gati with
    | Some g -> Printf.printf "// meend -> gati (%s) -> slide between notes\n" g
    | None -> ());
  if has "nyasa" then (match vriddhi with
    | Some v -> Printf.printf "// nyasa -> viraam -> held final note (*%s)\n" v
    | None -> ());
  if has "kan-swara" then Printf.printf "// kan-swara -> sparsha -> grace touch\n";
  if has "vriddhi-laya" then (match tivra with
    | Some t -> Printf.printf "// vriddhi-laya -> tivra -> intensity rising (.fast(%s))\n" t
    | None -> ());
  if has "kshaya-laya" then (match tivra with
    | Some t -> Printf.printf "// kshaya-laya -> manda -> intensity falling (.slow(%s))\n" t
    | None -> ())
