(* yantra_tokeniser.ml — tokenise_expr: string → string list.
   splits a tantra expression string into tokens, handling strings,
   comments, parens, brackets, and commas. *)

let tokenise_expr (s : string) : string list =
  let buf = Buffer.create 16 in
  let tokens = ref [] in
  let len = String.length s in
  let i = ref 0 in
  let flush () =
    if Buffer.length buf > 0 then begin
      tokens := Buffer.contents buf :: !tokens;
      Buffer.clear buf
    end
  in
  while !i < len do
    let c = s.[!i] in
    match c with
    | '-' when !i + 1 < len && s.[!i + 1] = '-' ->
      (* comment: skip rest of line *)
      flush ();
      while !i < len && s.[!i] <> '\n' do incr i done
    | ' ' | '\t' | '\n' ->
      flush (); incr i
    | '(' | ')' | '[' | ']' | ',' ->
       flush ();
       tokens := String.make 1 c :: !tokens;
       incr i
    | '"' ->
      (* string literal *)
      flush ();
      incr i;
      let sbuf = Buffer.create 16 in
      while !i < len && s.[!i] <> '"' do
        if s.[!i] = '\\' && !i + 1 < len then begin
          (match s.[!i + 1] with
           | 'n' -> Buffer.add_char sbuf '\n'; i := !i + 2
           | 't' -> Buffer.add_char sbuf '\t'; i := !i + 2
           | '\\' -> Buffer.add_char sbuf '\\'; i := !i + 2
           | '"' -> Buffer.add_char sbuf '"'; i := !i + 2
           | _ -> Buffer.add_char sbuf s.[!i]; incr i)
        end else begin
          Buffer.add_char sbuf s.[!i];
          incr i
        end
      done;
      if !i < len then incr i;  (* skip closing quote *)
      tokens := ("\"" ^ Buffer.contents sbuf ^ "\"") :: !tokens
    | _ ->
      Buffer.add_char buf c;
      incr i
  done;
  flush ();
  List.rev !tokens
