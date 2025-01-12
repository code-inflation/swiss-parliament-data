#!/bin/bash

base_url="https://ws-old.parlament.ch"
list_endpoint="/factions?format=json"
output_dir="factions_details"
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

mkdir -p "$output_dir"

curl -s -H "User-Agent: $user_agent" "$base_url$list_endpoint" | jq -c '.[]' | while read -r faction; do
  faction_id=$(echo "$faction" | jq -r '.id')

  details_endpoint="/factions/$faction_id?format=json"
  echo "Fetching details for faction ID: $faction_id"
  curl -s -H "User-Agent: $user_agent" "$base_url$details_endpoint" | \
    jq 'del(.updated) | .members |= map(del(.updated))' > "$output_dir/faction_$faction_id.json"
done

echo "Finished fetching all faction details."
