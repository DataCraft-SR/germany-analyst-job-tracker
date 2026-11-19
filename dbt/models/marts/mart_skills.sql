-- How often each tool is mentioned in live postings that have a description.
with described as (
    select role_family, skills
    from {{ ref('int_postings') }}
    where is_active and is_described and has_description
),

totals as (
    select role_family, count(*) as n_postings from described group by 1
    union all
    select 'All analyst roles', count(*) from described
),

mentions as (
    select role_family, unnest(skills) as skill from described
    union all
    select 'All analyst roles', unnest(skills) from described
)

select
    m.role_family,
    m.skill,
    count(*)                         as n_mentions,
    t.n_postings,
    count(*) / t.n_postings          as share_of_postings
from mentions m
join totals t using (role_family)
group by m.role_family, m.skill, t.n_postings
order by role_family, n_mentions desc
