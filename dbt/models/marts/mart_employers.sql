-- Employers with the most live analyst postings.
-- Staffing agencies are flagged so they can be told apart from direct employers.
select
    employer,
    count(*)                                         as live_postings,
    string_agg(distinct role_family, ', ' order by role_family) as role_families,
    regexp_matches(lower(employer),
        'personal|recruit|staffing|zeitarbeit|randstad|hays|adecco|manpower|gulp|amadeus fire|robert half|experis|brunel|tempton|orizon|dis ag|akkodis|ferchau'
    )                                                as is_staffing_agency
from {{ ref('int_postings') }}
where is_active and employer is not null
group by employer
order by live_postings desc
limit 50
