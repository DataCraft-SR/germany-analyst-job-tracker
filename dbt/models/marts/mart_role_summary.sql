-- Today's market by role family: volume, remote, language, entry-level, pay.
with active as (
    select * from {{ ref('int_postings') }} where is_active
),

by_role as (
    select
        role_family,
        count(*)                                                         as live_postings,
        avg(homeoffice_possible::int)                                    as share_remote_possible,
        avg(fulltime::int)                                               as share_fulltime,
        avg((seniority in ('Junior', 'Intern / Trainee', 'Working student'))::int) as share_entry_level,
        count(*) filter (where is_described)                             as n_described,
        avg((ad_language = 'en')::int) filter (where is_described and ad_language is not null)
                                                                         as share_english_ads,
        avg((german_requirement <> 'Fluent (C1+)')::int) filter (where is_described)
                                                                         as share_no_fluent_german,
        count(annual_salary_mid)                                         as n_with_salary,
        median(annual_salary_mid)                                        as median_salary
    from active
    group by role_family
)

select * from by_role
union all
select
    'All analyst roles',
    count(*),
    avg(homeoffice_possible::int),
    avg(fulltime::int),
    avg((seniority in ('Junior', 'Intern / Trainee', 'Working student'))::int),
    count(*) filter (where is_described),
    avg((ad_language = 'en')::int) filter (where is_described and ad_language is not null),
    avg((german_requirement <> 'Fluent (C1+)')::int) filter (where is_described),
    count(annual_salary_mid),
    median(annual_salary_mid)
from active
