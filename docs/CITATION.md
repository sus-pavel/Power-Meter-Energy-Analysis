# Citing PowerMeter

PowerMeter is research software. If you use it in a paper, technical report, laboratory demonstration, benchmark, thesis, or derived software project, cite the software repository and the relevant scientific publications.

## Software Citation

Recommended citation before DOI registration:

```text
Suslikov, P. (2026). PowerMeter: Open-source Modbus TCP energy monitoring platform with real-time dashboards, demand-response potential assessment, and SSA-based electrical load pattern analysis (v0.1.0) [Computer software]. GitHub. https://github.com/sus-pavel/PowerMeter
```

## BibTeX

```bibtex
@software{suslikov_powermeter_2026,
  author  = {Suslikov, Pavel},
  title   = {{PowerMeter}: Open-source Modbus TCP energy monitoring platform with real-time dashboards, demand-response potential assessment, and SSA-based electrical load pattern analysis},
  version = {0.1.0},
  year    = {2026},
  url     = {https://github.com/sus-pavel/PowerMeter},
  license = {MIT}
}
```

## Related Scientific Work

When citing a method implemented or discussed by PowerMeter, also cite the relevant publication:

- Zhukovskiy Y.L., Suslikov P.K. Identification and classification of electrical loads in mining enterprises based on signal decomposition methods. Journal of Mining Institute, 2025, Vol. 275, pp. 5-17.
- Suslikov P. A Cluster-Informed Demand Response Flexibility Index for Reconstructed Load Patterns. IEEE EDM 2026. DOI and IEEE Xplore page expected after publication of the conference proceedings.
- Zhukovskiy Y., Suslikov P., Rasputin D. NILM-Based Feedback for Demand Response: A Reproducible Binary State-Detection Algorithm Using Active Power. Electricity, 2026, 7(1), 23. DOI: 10.3390/electricity7010023.

## Future DOI Integration

For archival citation, connect the GitHub repository to Zenodo and enable automatic DOI generation for tagged releases. The recommended workflow is:

1. Create a GitHub release tag such as `v0.1.0`.
2. Enable Zenodo archiving for the repository.
3. Let Zenodo archive the release and issue a version-specific DOI.
4. Add the DOI to `CITATION.cff`, this document, and the GitHub release notes.
5. Use the version-specific DOI for papers and the concept DOI for general software references.
