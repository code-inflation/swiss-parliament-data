#!/bin/bash
set -euo pipefail

# Cleanup trap for temp files
cleanup() {
  rm -f "$tmp_groups" "$ids_file" 2>/dev/null || true
}
trap cleanup EXIT

base_url="https://api.openparldata.ch/v1"
groups_endpoint="/groups/"
memberships_endpoint="/memberships/"
output_dir="factions_details"
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
limit=1000

mkdir -p "$output_dir"

fetch_groups() {
  local offset=0
  while true; do
    local response
    response=$(curl -sf --retry 3 --retry-delay 5 -H "User-Agent: $user_agent" \
      "$base_url$groups_endpoint?type_harmonized_id=4&body_key=CHE&offset=$offset&limit=$limit")

    if [ $? -ne 0 ]; then
      echo "ERROR: curl failed for groups endpoint" >&2
      return 1
    fi

    # Validate JSON has .data array
    if ! echo "$response" | jq -e '.data' > /dev/null 2>&1; then
      echo "ERROR: Invalid JSON response from groups API" >&2
      return 1
    fi

    echo "$response" | jq -c '.data[] | select(.active == true)'
    local has_more
    has_more=$(echo "$response" | jq -r '.meta.has_more')
    if [ "$has_more" != "true" ]; then
      break
    fi
    offset=$((offset + limit))
  done
}

tmp_groups=$(mktemp)
fetch_groups > "$tmp_groups"

if [ ! -s "$tmp_groups" ]; then
  echo "ERROR: fetch_groups returned empty response" >&2
  rm -f "$tmp_groups"
  exit 1
fi

ids_file=$(mktemp)
jq -r '.external_alternative_id // empty' "$tmp_groups" | sort -u > "$ids_file"

# Count IDs from API
new_ids_count=$(wc -l < "$ids_file")
echo "Faction IDs from API: $new_ids_count"

# CRITICAL: Abort if API returned zero IDs
if [ "$new_ids_count" -eq 0 ]; then
  echo "ERROR: API returned 0 faction IDs. Aborting to prevent data loss." >&2
  rm -f "$tmp_groups" "$ids_file"
  exit 1
fi

for existing in "$output_dir"/faction_*.json; do
  if [ ! -e "$existing" ]; then
    continue
  fi
  existing_id=${existing##*/}
  existing_id=${existing_id#faction_}
  existing_id=${existing_id%.json}
  if ! grep -Fxq "$existing_id" "$ids_file"; then
    rm -f "$existing"
  fi
done

while read -r group; do
  group_id=$(echo "$group" | jq -r '.id')
  faction_id=$(echo "$group" | jq -r '.external_alternative_id // empty')
  faction_abbr=$(echo "$group" | jq -r '.abbreviation.de // empty')
  faction_name=$(echo "$group" | jq -r '.name.de // empty')

  if [ -z "$faction_id" ]; then
    echo "Skipping group ID $group_id: missing external_alternative_id"
    continue
  fi

  echo "Fetching memberships for faction ID: $faction_id (group ID: $group_id)"
  tmp_memberships=$(mktemp)
  offset=0
  while true; do
    response=$(curl -sf --retry 3 --retry-delay 5 -H "User-Agent: $user_agent" \
      "$base_url$memberships_endpoint?group_id=$group_id&expand=person&offset=$offset&limit=$limit")

    if [ $? -ne 0 ]; then
      echo "WARNING: curl failed for memberships of group $group_id at offset $offset" >&2
      break  # Continue to next faction rather than abort entirely
    fi

    echo "$response" | jq -c '.data[]' >> "$tmp_memberships"
    has_more=$(echo "$response" | jq -r '.meta.has_more')
    if [ "$has_more" != "true" ]; then
      break
    fi
    offset=$((offset + limit))
  done

  members_json=$(jq -s --arg faction_abbr "$faction_abbr" --arg faction_name "$faction_name" '
    def lang_field($value):
      if ($value | type) == "object" then
        ($value.de // null)
      else
        $value
      end;

    def canton_code($name):
      if $name == null then null
      elif $name == "Aargau" then "AG"
      elif $name == "Appenzell A.-Rh." or $name == "Appenzell Ausserrhoden" then "AR"
      elif $name == "Appenzell I.-Rh." or $name == "Appenzell Innerrhoden" then "AI"
      elif $name == "Basel-Landschaft" then "BL"
      elif $name == "Basel-Stadt" then "BS"
      elif $name == "Bern" then "BE"
      elif $name == "Freiburg" then "FR"
      elif $name == "Genf" then "GE"
      elif $name == "Glarus" then "GL"
      elif $name == "Graubünden" then "GR"
      elif $name == "Jura" then "JU"
      elif $name == "Luzern" then "LU"
      elif $name == "Neuenburg" then "NE"
      elif $name == "Nidwalden" then "NW"
      elif $name == "Obwalden" then "OW"
      elif $name == "Schaffhausen" then "SH"
      elif $name == "Schwyz" then "SZ"
      elif $name == "Solothurn" then "SO"
      elif $name == "St. Gallen" or $name == "Sankt Gallen" then "SG"
      elif $name == "Tessin" then "TI"
      elif $name == "Thurgau" then "TG"
      elif $name == "Uri" then "UR"
      elif $name == "Waadt" then "VD"
      elif $name == "Wallis" then "VS"
      elif $name == "Zug" then "ZG"
      elif $name == "Zürich" then "ZH"
      else null
      end;

    def council_code($sector):
      if $sector == "NR" then "N"
      elif $sector == "SR" then "S"
      else null
      end;

    def faction_function($role):
      if $role == "Mitglied" then 1
      elif $role == "Präsident/in" then 2
      elif $role == "Vizepräsident/in" then 11
      else null
      end;

    map(
      . as $membership
      | ($membership.person.data[0] // empty) as $person
      | {
          id: ($person.id // null),
          canton: canton_code(lang_field($person.electoral_district)),
          cantonName: lang_field($person.electoral_district),
          council: council_code($person.parliament_sector // null),
          faction: $faction_abbr,
          factionName: $faction_name,
          firstName: ($person.firstname // null),
          lastName: ($person.lastname // null),
          number: (if ($person.external_alternative_id // null) == null then null else ($person.external_alternative_id | tonumber) end),
          party: lang_field($person.party),
          partyName: lang_field($person.party_harmonized),
          active: ($membership.active // null),
          code: null,
          gender: ($person.gender // null),
          officialDenomination: null,
          salutationLetter: null,
          salutationTitle: null,
          factionFunction: faction_function(lang_field($membership.role_name))
        }
    )' "$tmp_memberships")

  rm -f "$tmp_memberships"

  jq -n \
    --arg faction_id "$faction_id" \
    --arg faction_abbr "$faction_abbr" \
    --arg faction_name "$faction_name" \
    --argjson members "$members_json" \
    '{
      id: ($faction_id | tonumber),
      abbreviation: $faction_abbr,
      code: ("FRA_" + $faction_id + "_"),
      members: $members,
      name: $faction_name,
      shortName: ("Fraktion " + $faction_abbr)
    }' > "$output_dir/faction_$faction_id.json"
done < "$tmp_groups"

rm -f "$tmp_groups" "$ids_file"

echo "Finished fetching all faction details."
