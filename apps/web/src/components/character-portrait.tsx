export function CharacterPortrait({id, name = 'Explorer'}: {id?: string | null; name?: string}) {
  return id
    ? <img className="character-portrait" src={`/portraits/${encodeURIComponent(id)}.svg`} alt=""/>
    : <span aria-hidden="true">{name.slice(0, 1)}</span>;
}
