-- Features derived from each posting's description (one row per posting).
{% if files_exist(var("features_glob")) %}
select
    refnr,
    cast(fetched_at as timestamp)    as fetched_at,
    has_description,
    description_chars,
    ad_language,
    german_requirement,
    skills
from read_json(
    '{{ var("features_glob") }}',
    format = 'newline_delimited',
    columns = {
        refnr: 'VARCHAR', fetched_at: 'VARCHAR', has_description: 'BOOLEAN',
        description_chars: 'INTEGER', ad_language: 'VARCHAR',
        german_requirement: 'VARCHAR', skills: 'VARCHAR[]'
    }
)
qualify row_number() over (partition by refnr order by fetched_at desc) = 1
{% else %}
select
    null::varchar as refnr, null::timestamp as fetched_at, null::boolean as has_description,
    null::integer as description_chars, null::varchar as ad_language,
    null::varchar as german_requirement, null::varchar[] as skills
where false
{% endif %}
