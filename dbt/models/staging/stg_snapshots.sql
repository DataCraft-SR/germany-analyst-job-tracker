-- One row per posting per day it was live on the job board.
with src as (
    select *
    from read_json(
        '{{ var("raw_glob") }}',
        format = 'newline_delimited',
        columns = {
            snapshot_date: 'DATE', refnr: 'VARCHAR', title: 'VARCHAR',
            role_family: 'VARCHAR', seniority: 'VARCHAR', employer: 'VARCHAR',
            occupation: 'VARCHAR', city: 'VARCHAR', postcode: 'VARCHAR',
            region: 'VARCHAR', country: 'VARCHAR', lat: 'DOUBLE', lon: 'DOUBLE',
            n_locations: 'INTEGER', first_published: 'VARCHAR', modified_at: 'VARCHAR',
            start_date: 'VARCHAR', contract: 'VARCHAR', fulltime: 'BOOLEAN',
            parttime: 'BOOLEAN', minijob: 'BOOLEAN', career_changer_ok: 'BOOLEAN',
            homeoffice_possible: 'BOOLEAN', homeoffice_type: 'VARCHAR',
            homeoffice_pct: 'DOUBLE', salary_unit: 'VARCHAR', salary_min: 'DOUBLE',
            salary_max: 'DOUBLE', is_external: 'BOOLEAN', search_terms: 'VARCHAR[]'
        }
    )
),

typed as (
    select
        snapshot_date,
        refnr,
        title,
        role_family,
        seniority,
        nullif(trim(employer), '')                         as employer,
        occupation,
        -- 'München' and 'München, Isar' etc. -> 'München'
        trim(split_part(city, ',', 1))                     as city,
        postcode,
        coalesce(rn.state_name, src.region)               as region,
        country,
        lat,
        lon,
        n_locations,
        try_cast(left(first_published, 10) as date)       as first_published,
        try_cast(left(start_date, 10) as date)            as start_date,
        contract,
        fulltime,
        parttime,
        minijob,
        career_changer_ok,
        homeoffice_possible,
        homeoffice_type,
        homeoffice_pct,
        salary_unit,
        salary_min,
        salary_max,
        -- Normalise to an annual figure so ranges are comparable
        case salary_unit
            when 'JAHRESGEHALT' then 1
            when 'MONATSGEHALT' then 12
        end                                                as salary_multiplier,
        is_external,
        search_terms
    from src
    left join {{ ref('region_names') }} rn on rn.region_code = src.region
    where refnr is not null
)

select
    * exclude (salary_multiplier),
    case
        when salary_multiplier is not null and salary_min is not null
        then ((salary_min + coalesce(salary_max, salary_min)) / 2) * salary_multiplier
    end as annual_salary_mid_raw
from typed
-- the same posting can appear twice if a day is re-run; keep one
qualify row_number() over (partition by snapshot_date, refnr order by refnr) = 1
