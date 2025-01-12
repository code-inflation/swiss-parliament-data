#!/bin/bash

base_url="https://ws-old.parlament.ch"

list_endpoint="/factions?format=json"

output_dir="factions_details"

mkdir -p "$output_dir"

curl -s -H "User-Agent: Mozilla/5.0" "$base_url$list_endpoint" | jq -c '.[]' | while read -r faction; do
  echo "Fetching details for faction ID: $faction_id"
  faction_id=$(echo "$faction" | jq -r '.id')
  details_endpoint="/factions/$faction_id?format=json"
  curl -s -H "User-Agent: Mozilla/5.0" "$base_url$details_endpoint" | jq . > "$output_dir/faction_$faction_id.json"
done

echo "Finished fetching all faction details."
