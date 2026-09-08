//! Read-only consistency checks for the active persistence-policy bundle.
//! This is not TypeSpec/JSON Schema compilation or database certification.
use std::{env, fs, process};

const FILES: [&str; 5] = [
    "docs/PERSISTENCE_AUTHORITY.md",
    "agents.md",
    "AGENTS.md",
    "REPOSITORY_BOUNDARIES.md",
    "docs/PERSISTENCE_DUAL_SOURCE.md",
];
const BEGIN: &str = "<!-- persistence-authority:begin -->";
const END: &str = "<!-- persistence-authority:end -->";
type Documents = [Option<String>; 5];

#[derive(Debug, PartialEq, Eq)]
enum Outcome { NotApplicable, Consistent }
#[derive(Debug, PartialEq, Eq)]
enum PolicyError {
    Read(&'static str), MissingDocument(&'static str), MissingAuthority,
    MalformedBlock, MissingBlock, MirrorDrift, ObsoleteHierarchy,
    InvalidOwnership, MissingPeerRule, RevisionDrift, AliasDrift,
}

fn block(text: &str) -> Result<Option<&str>, PolicyError> {
    match (text.matches(BEGIN).count(), text.matches(END).count()) {
        (0, 0) => return Ok(None),
        (1, 1) => (),
        _ => return Err(PolicyError::MalformedBlock),
    }
    let start = text.find(BEGIN).ok_or(PolicyError::MalformedBlock)? + BEGIN.len();
    let end = text.find(END).ok_or(PolicyError::MalformedBlock)?;
    if start > end { return Err(PolicyError::MalformedBlock); }
    return Ok(Some(text[start..end].trim()));
}

fn revision(text: &str) -> Option<String> {
    let lower = text.to_ascii_lowercase();
    let words: Vec<&str> = lower.split(|c: char| !c.is_ascii_alphanumeric())
        .filter(|word| !word.is_empty()).collect();
    return words.windows(2).find_map(|pair| {
        if pair[0] == "revision" && pair[1].len() == 1
            && pair[1].bytes().all(|b| b.is_ascii_lowercase()) {
            return Some(pair[1].to_string());
        }
        return None;
    });
}

fn unique_line<'a>(text: &'a str, prefix: &str) -> Result<&'a str, PolicyError> {
    let lines: Vec<&str> = text.lines().filter(|line| line.starts_with(prefix)).collect();
    if lines.len() != 1 { return Err(PolicyError::InvalidOwnership); }
    return Ok(lines[0]);
}

fn repository_name(authority: &str, label: &str) -> Result<String, PolicyError> {
    let line = unique_line(authority, label)?;
    let rest = line.split_once("https://github.com/")
        .ok_or(PolicyError::InvalidOwnership)?.1;
    let repo = rest.split_once(')').ok_or(PolicyError::InvalidOwnership)?.0;
    let parts: Vec<&str> = repo.split('/').collect();
    if parts.len() != 2 || parts.iter().any(|part| part.is_empty()
        || !part.bytes().all(|b| b.is_ascii_alphanumeric() || b"-_.".contains(&b))) {
        return Err(PolicyError::InvalidOwnership);
    }
    return Ok(parts[1].to_string());
}

fn validate(docs: &Documents) -> Result<Outcome, PolicyError> {
    let lower = block(docs[1].as_deref().unwrap_or(""))?;
    let upper = block(docs[2].as_deref().unwrap_or(""))?;
    let Some(authority) = docs[0].as_deref() else {
        if lower.is_some() || upper.is_some() || docs[4].is_some()
            || docs[3].as_deref().unwrap_or("").contains("## Persistence contracts") {
            return Err(PolicyError::MissingAuthority);
        }
        return Ok(Outcome::NotApplicable);
    };
    for index in 1..4 {
        if docs[index].is_none() { return Err(PolicyError::MissingDocument(FILES[index])); }
    }
    let lower = lower.ok_or(PolicyError::MissingBlock)?;
    let upper = upper.ok_or(PolicyError::MissingBlock)?;
    if lower != upper { return Err(PolicyError::MirrorDrift); }
    let lowered = lower.to_ascii_lowercase();
    if lowered.split(|c: char| !c.is_ascii_alphanumeric()).any(|s| s == "p0" || s == "p1")
        || lowered.contains("secondary-primary") || lowered.contains("canonical ast") {
        return Err(PolicyError::ObsoleteHierarchy);
    }
    let source = repository_name(authority, "**Contract sources:**")?;
    let release = repository_name(authority, "**Desired-state release:**")?;
    let runtime = repository_name(authority, "**Runtime boundary:**")?;
    let apply = repository_name(authority, "**Migration execution:**")?;
    let names = [&source, &release, &runtime, &apply];
    for (index, name) in names.iter().enumerate() {
        if names[index + 1..].contains(name) { return Err(PolicyError::InvalidOwnership); }
    }
    for (label, name) in [
        ("- **Peer source A:**", &source), ("- **Peer source B:**", &source),
        ("- **Certified release:**", &release), ("- **Runtime:**", &runtime),
        ("- **Apply:**", &apply),
    ] {
        if !unique_line(lower, label)?.contains(&format!("`{name}`")) {
            return Err(PolicyError::InvalidOwnership);
        }
    }
    for phrase in [
        "independently authored persistence TypeSpec",
        "independently authored persistence JSON Schema/OpenAPI",
        "Neither peer is derived from, subordinate to, or overwritten by the other.",
        "pins both peer sources", "Disagreement blocks release", "alone owns reviewed",
        "no DDL at API/web boot",
    ] {
        if !lower.contains(phrase) { return Err(PolicyError::MissingPeerRule); }
    }
    let boundaries = docs[3].as_deref().ok_or(PolicyError::MissingDocument(FILES[3]))?;
    if !boundaries.contains(&format!("`{source}` owns independently authored"))
        || names.iter().any(|name| !boundaries.contains(&format!("`{name}`"))) {
        return Err(PolicyError::InvalidOwnership);
    }
    let expected_revision = revision(authority).ok_or(PolicyError::RevisionDrift)?;
    if revision(lower).as_deref() != Some(expected_revision.as_str()) {
        return Err(PolicyError::RevisionDrift);
    }
    if let Some(alias) = &docs[4] {
        if !alias.contains("[PERSISTENCE_AUTHORITY.md](PERSISTENCE_AUTHORITY.md)")
            && !alias.contains("[`PERSISTENCE_AUTHORITY.md`](PERSISTENCE_AUTHORITY.md)") {
            return Err(PolicyError::AliasDrift);
        }
        if let Some(alias_revision) = revision(alias) {
            if alias_revision != expected_revision { return Err(PolicyError::AliasDrift); }
        }
    }
    return Ok(Outcome::Consistent);
}

fn read_document(path: &'static str) -> Result<Option<String>, PolicyError> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(value) => value,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(_) => return Err(PolicyError::Read(path)),
    };
    if !metadata.is_file() || metadata.len() > 262_144 { return Err(PolicyError::Read(path)); }
    let text = fs::read_to_string(path).map_err(|_| PolicyError::Read(path))?;
    if text.len() > 262_144 { return Err(PolicyError::Read(path)); }
    return Ok(Some(text.replace("\r\n", "\n")));
}

fn run() -> Result<Outcome, PolicyError> {
    let mut docs: Documents = std::array::from_fn(|_| None);
    for (index, path) in FILES.iter().enumerate() { docs[index] = read_document(path)?; }
    return validate(&docs);
}

fn main() {
    // This repository check has no configuration flags or alternate argv parser.
    if env::args_os().len() != 1 {
        eprintln!("persistence-policy: arguments are not accepted");
        process::exit(2);
    }
    match run() {
        Ok(Outcome::NotApplicable) => println!("persistence-policy: NOT_APPLICABLE (no active authority bundle)"),
        Ok(Outcome::Consistent) => println!("persistence-policy: CONSISTENT (documentation only; runtime/contract parity not certified)"),
        Err(error) => { eprintln!("persistence-policy: {error:?}"); process::exit(1); }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn valid() -> Documents {
        let authority = "revision i\n**Contract sources:** [source](https://github.com/example/demo-interfaces)\n**Desired-state release:** [release](https://github.com/example/demo-lib-core)\n**Runtime boundary:** [runtime](https://github.com/example/demo-orm-core)\n**Migration execution:** [apply](https://github.com/example/demo-infra)\n";
        let agents = format!("{BEGIN}\n- **Peer source A:** independently authored persistence TypeSpec in `demo-interfaces`.\n- **Peer source B:** independently authored persistence JSON Schema/OpenAPI in `demo-interfaces`. Neither peer is derived from, subordinate to, or overwritten by the other.\n- **Certified release:** `demo-lib-core` pins both peer sources. Disagreement blocks release.\n- **Runtime:** `demo-orm-core`\n- **Apply:** `demo-infra` alone owns reviewed DPM; no DDL at API/web boot.\nrevision i\n{END}");
        return [Some(authority.into()), Some(agents.clone()), Some(agents),
            Some("`demo-interfaces` owns independently authored contracts; `demo-lib-core`, `demo-orm-core`, `demo-infra` keep separate roles.".into()),
            Some("[`PERSISTENCE_AUTHORITY.md`](PERSISTENCE_AUTHORITY.md)".into())];
    }
    fn replace(docs: &mut Documents, index: usize, from: &str, to: &str) {
        docs[index] = Some(docs[index].as_ref().unwrap().replace(from, to));
    }
    fn pair(docs: &mut Documents, from: &str, to: &str) {
        replace(docs, 1, from, to); replace(docs, 2, from, to);
    }
    macro_rules! rejects {
        ($name:ident, $change:expr, $error:expr) => {
            #[test] fn $name() {
                let mut docs = valid(); ($change)(&mut docs);
                assert_eq!(validate(&docs), Err($error));
            }
        };
    }
    #[test] fn valid_bundle_passes() { assert_eq!(validate(&valid()), Ok(Outcome::Consistent)); }
    #[test] fn absent_bundle_is_explicitly_not_applicable() {
        assert_eq!(validate(&std::array::from_fn(|_| None)), Ok(Outcome::NotApplicable));
    }
    #[test] fn unrelated_priority_labels_outside_block_are_allowed() {
        let mut docs = valid();
        for index in [1, 2] { docs[index] = Some(format!("P0 incident priority\n{}", docs[index].as_ref().unwrap())); }
        assert_eq!(validate(&docs), Ok(Outcome::Consistent));
    }
    rejects!(orphan_bundle_fails, |d: &mut Documents| d[0] = None, PolicyError::MissingAuthority);
    rejects!(missing_mirror_fails, |d: &mut Documents| d[2] = None, PolicyError::MissingDocument("AGENTS.md"));
    rejects!(missing_block_fails, |d: &mut Documents| d[2] = Some("instructions".into()), PolicyError::MissingBlock);
    rejects!(duplicate_block_fails, |d: &mut Documents| pair(d, END, &format!("{END}{BEGIN}x{END}")), PolicyError::MalformedBlock);
    rejects!(unterminated_block_fails, |d: &mut Documents| pair(d, END, ""), PolicyError::MalformedBlock);
    rejects!(reversed_markers_fail, |d: &mut Documents| pair(d, BEGIN, END), PolicyError::MalformedBlock);
    rejects!(mirror_drift_fails, |d: &mut Documents| replace(d, 2, "revision i", "revision j"), PolicyError::MirrorDrift);
    rejects!(p0_hierarchy_fails, |d: &mut Documents| pair(d, "revision i", "P0: TypeSpec\nrevision i"), PolicyError::ObsoleteHierarchy);
    rejects!(p1_hierarchy_fails, |d: &mut Documents| pair(d, "revision i", "P1: JSON Schema\nrevision i"), PolicyError::ObsoleteHierarchy);
    rejects!(canonical_ast_fails, |d: &mut Documents| pair(d, "revision i", "canonical AST\nrevision i"), PolicyError::ObsoleteHierarchy);
    rejects!(wrong_contract_owner_fails, |d: &mut Documents| pair(d, "in `demo-interfaces`", "in `demo-lib-core`"), PolicyError::InvalidOwnership);
    rejects!(missing_independence_fails, |d: &mut Documents| pair(d, "Neither peer is derived from, subordinate to, or overwritten by the other.", ""), PolicyError::MissingPeerRule);
    rejects!(missing_release_veto_fails, |d: &mut Documents| pair(d, "Disagreement blocks release", "Ignore disagreements"), PolicyError::MissingPeerRule);
    rejects!(boundary_owner_drift_fails, |d: &mut Documents| replace(d, 3, "`demo-interfaces` owns", "`demo-lib-core` owns"), PolicyError::InvalidOwnership);
    rejects!(revision_drift_fails, |d: &mut Documents| pair(d, "revision i", "revision f"), PolicyError::RevisionDrift);
    rejects!(stale_alias_fails, |d: &mut Documents| d[4].as_mut().unwrap().push_str(" revision f"), PolicyError::AliasDrift);
    rejects!(bad_alias_target_fails, |d: &mut Documents| replace(d, 4, "PERSISTENCE_AUTHORITY.md", "WRONG.md"), PolicyError::AliasDrift);
    rejects!(missing_role_metadata_fails, |d: &mut Documents| replace(d, 0, "**Runtime boundary:**", "**Old runtime:**"), PolicyError::InvalidOwnership);
    rejects!(duplicate_role_metadata_fails, |d: &mut Documents| d[0].as_mut().unwrap().push_str("**Runtime boundary:** [runtime](https://github.com/example/demo-orm-core)\n"), PolicyError::InvalidOwnership);
}
