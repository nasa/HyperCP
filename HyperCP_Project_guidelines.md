# Guidelines for Collaboration on the HyperInSPACE Community Processor (HyperCP)

1. **Introduction**

    HyperCP is an open science, open-source Collaboration to facilitate community development of a processor for in situ 
    above-water radiometry for aquatic biogeochemistry applications, algorithm development and satellite validations. The 
    Collaboration aims to achieve the highest quality in situ measurement processing, extensions to new field instrument 
    platforms, measurement uncertainty propagation according to metrological standards, and other improvements to the 
    algorithms and the processor package.
    
    The Collaboration is initiated staring from an existing NASA tool called HyperInSPACE 
    (https://github.com/nasa/HyperInSPACE). HyperInSPACE has been developed as an open-source and open science processor to 
    standardize the processing and quality control of hyperspectral above-water measurements from Sea-Bird radiometers for
    preservation in the publicly open NASA SeaBASS archive.
    Additionally the more recent [Copernicus’ Ocean Colour Data Base](https://ocdb.eumetsat.int), fully compatible with 
    SeaBASS in terms of input format and in turn with the CSV HyperCP output - is an additional key target database to 
    ensure long-term preservation.
    HyperInSPACE has been designed to adhere to the best practices
    detailed in the legacy [NASA Ocean Optics Protocols](https://oceancolor.gsfc.nasa.gov/docs/technical/) 
    (Mueller et al., 2003) and to incorporate the advances defined in
    the [IOCCG Optical Radiometry Protocols](https://ioccg.org/what-we-do/ioccg-publications/ocean-optics-protocols-satellite-ocean-colour-sensor-validation/)
    (Zibordi et al., 2019). HyperInSPACE was released publicly in March 2021 and its
    subsequent evolutions included contributions from University of Maine and the community. In May 2021, NASA and EUMETSAT 
    came into agreement about further extensions of the processor to include TriOS radiometers and measurement uncertainty
    propagation in the frame of the [FRM4SOC-2](https://frm4soc2.eumetsat.int/) activity supported by the EC Copernicus Programme.
    
    HyperInSPACE was originally adapted from an open-source, robust, Python processor developed by the University of 
    Victoria and called [PySciDon](https://ieeexplore.ieee.org/document/8121926) (Vandenberg et al. 2017). PySciDon was
    established to replace Satlantic’s (now Sea-Bird’s) proprietary ProSoft software package for processing autonomous,
     above-water radiometry data from a ferry-based Sea-Bird 
    HyperSAS SolarTracker platform. HyperCP development partners under this Collaboration, as defined in these Guidelines,
    comprise the HyperCP Project. The goal of the Project is to expand community engagement and collaboration, and to manage
    and support the processor development
    effort.
    
    The initial partners include NASA, EUMETSAT and FRM4SOC-2 affiliates, NPL and ACRI-ST, who were joined in 2023 by 
    University of Victoria and University of Maine.
    
    See [Appendix](HyperCP_Project_guidelines_APPENDIX.md) for up-to-date list of all Collaborators.

1. **Community Support and Management of Community Contributions**

    1. User support and the HyperCP Project can be reached using the Discussion feature of the GitHub repository.

    1. HyperCP is in its concept a Community Processor and ad hoc or regular community contributions to the HyperCP package
    are highly encouraged. Reviews or revisions of the existing implementations are also solicited. The GitHub Issue feature
    should be used to initiate a contribution or highlight a software issue. Further details are provided in Section 3.v.
    
    1. Members of the community, institutions and agencies are welcome to join the HyperCP Project. To join, a short
    proposal is required, which shall include a description of intended contributions, their time frame and expected
    organization of work, or a description of existing contributions and their possibility for ingesting into the HyperCP
    package. Proposals shall be addressed to the co-chairs listed in the [Appendix](HyperCP_Project_guidelines_APPENDIX.md).
    
    1. Community contributions and HyperCP Project membership proposals are checked, validated, and approved by the HyperCP
    Project under the leadership of its co-chairs. The contributors may be invited to HyperCP Project Meetings to 
    participate in technical and/or administrative discussions.

1. **HyperCP Management**

    1. To coordinate the development of new features in the HyperCP by collaboration
    contributors, HyperCP Project Meetings will be held between principal software
    developers at a cadence to be decided on an ongoing basis depending on the number
    and complexity of the updates and issues. HyperCP external contributors and
    collaborators may also be invited to participate as appropriate. At the initial
    inception, NASA and EUMETSAT will take a lead in co-chairing and organizing
    the Project Meetings. Subsequent meetings can be coordinated by other HyperCP
    Project members, potentially on a rotating basis.
    
    1. As an open-source community processor, HyperCP has no “ownership” and no
    organizations or individuals hold a “gate keeper” role with respect to its evolution.
    Anyone is free to create clones of the master Git repository for offline development
    however they see fit. HyperCP may be adapted to develop derivative products, but
    such products should be clearly distinguished from HyperCP as such to avoid
    confusion of provenance for the users and the scientific community. Derivative
    projects should clearly acknowledge HyperCP and contributors as outlined below
    in section 4, and clearly state that these derivatives are removed from any oversite
    or review associated with this HyperCP.
    
    1. For HyperCP dissemination, there is one authorized HyperCP Project public master
    repository: https://github.com/nasa/HyperInSPACE. The single repository
    provides a stable location for the community to acquire the software and to ensure
    the quality of HyperCP implementation. The quality of the repository is assured by
    the expertise of the Project members, management by consensus, administration of
    community contributions, software maintenance and version update, as well as
    continuing user support.
    The designated HyperCP GitHub master repository is located at NASA as it has a
    longstanding history of community engagement and official open-source hosting
    and dissemination through NASA’s Software Release System reviews and
    approvals. Alternatives to the NASA’s repository may be considered in the future
    in the frame of international coordination.
    
    1. All HyperCP Project partners are required to contribute to the development and
    evaluation of the HyperCP in a manner consistent with open science principles, e.g.,
    ([National Academies of Sciences 2018; UNESCO 2021](https://unesdoc.unesco.org/ark:/48223/pf0000379949.locale=en)).
    This includes maximizing transparency, accessibility, and reproducibility of software
    contributions and functionality as well as adherence to intellectual integrity and
    respect for ethical principles pertaining to research.
    
    1. Software update logistics: HyperCP Project members and external agreed
    contributors, as confirmed at the regular HyperCP Project Meetings, shall follow
    the guidance in this section for submitting updates to the HyperCP GitHub
    repository.
    
        1. The following is a set of recommendations for how software updates will
        be managed but should be updated over time as the contributing parties
        become more familiar with the possibilities and pitfalls of open-source
        collaboration in a Git environment.
        
        1. Contributing developers should fork and/or clone the master repository
        from the NASA GitHub and pull updates from master before making any
        new updates to limit merge conflicts.
        
        1. Updates should, as much as possible, address issues identified in the NASA
        GitHub repository Issues feature. Issues may be submitted by any
        contributor or outside party.
        
        1. Contributors should, as much as possible, address small, incremental issues
        to avoid merge conflicts with large overhauls of source code, and submit
        numerous, small updates frequently rather than large, complex updates after
        long intervals to limit merge conflicts.
        
        1. When contributors are ready to send updates to the master repository, they
        should follow these steps:
    
            1. Create a fork from the master branch at
            (https://github.com/nasa/HyperInSPACE)
            
            1. Create sensibly named branch for the updates made to that fork (if a
            fork for that issue/update already exists on NASA GitHub, use that
            name).
            
            1. Commit all updates to the fork branch and push them to the GitHub
            fork repository
            
            1. Submit a pull request (PR) associated with the Issue to the branch
            of the same name on the principal GitHub repository  not the
            master branch  as described in the next section.
    
    1. Submitting PRs (adapted from the Core Flight System project)
    
        1. For the title, use the title convention Fix #XYZ,
        SHORT_DESCRIPTION. #XYZ should refer to the Issue number
        identified in the repository.
        
        1. Describe the contribution. First document which issue number was
        fixed using the template "Fix #XYZ". Then describe the
        contribution.
        
        1. Provide what testing was used to confirm the pull request resolves
        the link issue. If writing new code, also provide the associated
        coverage unit tests.
        
        1. Provide the expected behavior changes of the pull request.
        
        1. Provide the system the bug was observed on, if applicable, including
        the hardware, operating system(s), and versions.
        
        1. Provide any additional context if applicable.
        
        1. Provide your full name and/or GitHub username and your company
        or organization if applicable.
        
        1. Verify that the PR passes all workflow checks. If you expect some
        of these checks to fail, please note it in the Pull Request text or
        comments.
    
    1. HyperCP Project participants will review PRs and discuss at the next
    HyperCP Project Meeting  if not sufficiently agreed to by email  to
    determine whether the PR will be accepted or returned for edits. Once
    accepted in GitHub, the branch will become public (if it was not already),
    and then will be merged with the master repository. The Changelog.md file
    will be updated to reflect the description of the changes and the contributor
    who submitted them.

1. Acknowledgements and Public Presentation

    1. Recommendation for users:
    
        1. Always cite the HyperCP key papers listed in [Appendix](HyperCP_Project_guidelines_APPENDIX.md) in any publications
        in which the data presented were processed with HyperCP.
        
        1. In public presentations, include the HyperCP logo.
        
        1. When publishing results from HyperCP or requesting support, the version
        number and commit code (or date of most recent update/pull) should be
        noted.
    
    1. Recommendation for the members of the HyperCP Project:
    
        1. To avoid confusion within the community between this HyperCP Project,
        the legacy HyperInSPACE repository, the FRM4SOC2 “CP” development
        repository, and any other potential derivative versions going forward, the
        name “HyperCP” or “HyperInSPACE Community Processor” should be
        used in public presentations of the software or results deriving from the
        software.
        
        1. Acknowledgement statement in the HyperCP’s README shall be as in
        [Appendix](HyperCP_Project_guidelines_APPENDIX.md).
        
        1. In the case of oral or poster presentations from members of the HyperCP
        Project presenting to externals, the logos of all the involved institutions shall
        be visually identifiable. The full list of people and institutions involved in
        the HyperCP Project will be maintained in the [Appendix](HyperCP_Project_guidelines_APPENDIX.md).
        
        1. Acknowledgements of all people and institutions submitting significant
        contributions to the software will be made in software release notes and/or
        similar reports or documents that can be readily cited (e.g., with a DOI) in
        publications and presentations. See [Appendix](HyperCP_Project_guidelines_APPENDIX.md) for the most up-to-date
        acknowledgement statement, both for users and for internal use.

## References

Mueller, J. L. and others 2003. Ocean Optics Protocols for Satellite Ocean Color Sensor
Validation, Revision 4, Volume III. In J. L. Mueller [ed.], Ocean Optics Protocols for
Satellite Ocean Color Sensor Validation. NASA Goddard Space Flight Center.
National Academies of Sciences, E., and Medicine. 2018. Open Source Software Policy Options
for NASA Earth and Space Sciences. The National Academies Press.

Ruddick, K. G. and others 2019a. A Review of Protocols for Fiducial Reference Measurements of
Downwelling Irradiance for the Validation of Satellite Remote Sensing Data over Water.
Remote Sensing 11: 1742.

Ruddick, K. G. and others 2019b. A Review of Protocols for Fiducial Reference Measurements of
Water-Leaving Radiance for Validation of Satellite Remote-Sensing Data over Water.
Remote Sensing 11: 2198.

UNESCO. 2021. Draft Recommendation on Open Science. In U. S. Committee [ed.], UNESCO
General Conference, 41st Sesssion.

Vandenberg, N.; Costa, M.; Coady, Y.; Agbaje, T. (2017). PySciDON: A Python Scientific Framework for Development of
Ocean Network Applications. Proceedings. 2017 IEEE Pacific Rim Conference on Communications, Computers and Signal
Processing, 2017. Pp1-6.  DOI: 10.1109/PACRIM.2017.8121926. 

Zibordi, G., K. J. Voss, B. Johnson, and J. L. Mueller. 2019. Protocols for Satellite Ocean Colour
Data Validation: In Situ Optical Radiometry. In IOCCG [ed.], IOCCG Ocean Optics and
Biogeochemistry Protocols for Satellite Ocean Colour Sensor Validation. IOCCG.