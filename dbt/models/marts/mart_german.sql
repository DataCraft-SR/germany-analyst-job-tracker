-- German-language requirement by role family (live, described postings).
select
    role_family,
    german_requirement,
    count(*)                                                    as n_postings,
    count(*) / sum(count(*)) over (partition by role_family)    as share
from {{ ref('int_postings') }}
where is_active and is_described and has_description
group by role_family, german_requirement
order by role_family, n_postings desc
