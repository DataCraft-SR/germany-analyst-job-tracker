-- One row per posting: latest attributes, lifetime on the board, description features.
with latest_day as (
    select max(snapshot_date) as d from {{ ref('stg_snapshots') }}
),

life as (
    select
        refnr,
        min(snapshot_date)   as first_seen,
        max(snapshot_date)   as last_seen,
        count(*)             as days_seen
    from {{ ref('stg_snapshots') }}
    group by refnr
),

latest as (
    select *
    from {{ ref('stg_snapshots') }}
    qualify row_number() over (partition by refnr order by snapshot_date desc) = 1
)

select
    l.* exclude (snapshot_date, annual_salary_mid_raw),
    case
        when l.annual_salary_mid_raw between {{ var('salary_floor') }} and {{ var('salary_ceiling') }}
        then l.annual_salary_mid_raw
    end                                        as annual_salary_mid,
    life.first_seen,
    life.last_seen,
    life.days_seen,
    life.last_seen = latest_day.d              as is_active,
    f.has_description,
    f.ad_language,
    coalesce(f.german_requirement, 'Not checked yet') as german_requirement,
    f.skills,
    f.refnr is not null                        as is_described
from latest l
join life using (refnr)
cross join latest_day
left join {{ ref('stg_features') }} f using (refnr)
