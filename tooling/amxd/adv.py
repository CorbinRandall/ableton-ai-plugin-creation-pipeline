"""Build Ableton Device Preset (.adv) wrappers for .amxd devices."""

from __future__ import annotations

import os
from pathlib import Path

from paths import WORKSPACE, _user_lib_presets


def build_adv(spec: dict, amxd_deploy_path: Path, output: Path | None = None) -> Path:
    """Build an .adv (Ableton Device Preset) that wraps the .amxd with parameter definitions.

    Live reads parameters from the .adv XML, not the .amxd JSON.
    Without an .adv, only 'Device On' shows up.
    """
    import gzip

    name = spec.get("name", "Untitled")
    device_type = spec.get("device_type", "midi_effect")

    # Device class tag in Ableton XML
    device_class = {
        "midi_effect":  "MxDeviceMidiEffect",
        "audio_effect": "MxDeviceAudioEffect",
        "instrument":   "MxDeviceInstrument",
    }.get(device_type, "MxDeviceMidiEffect")

    # Collect parameters from spec boxes that have parameter_enable
    params = []
    for b in spec.get("boxes", []):
        box = b.get("box", {})
        if not box.get("parameter_enable"):
            continue
        saa = box.get("saved_attribute_attributes", {})
        vo = saa.get("valueof", {})
        if not vo.get("parameter_longname"):
            continue
        params.append({
            "name": vo["parameter_longname"],
            "shortname": vo.get("parameter_shortname", vo["parameter_longname"]),
            "min": vo.get("parameter_mmin", 0.0),
            "max": vo.get("parameter_mmax", 1.0),
            "default": vo.get("parameter_initial", [0.0])[0] if isinstance(vo.get("parameter_initial"), list) else vo.get("parameter_initial", 0.0),
            "type": vo.get("parameter_type", 0),  # 0=float, 2=enum
            "obj_id": box.get("id", ""),
        })

    # Build parameter XML
    param_xml = ""
    for i, p in enumerate(params):
        default_val = p["default"] if p["default"] is not None else p["min"]
        param_xml += f"""
				<MxDFloatParameter Id="{i}">
					<Index Value="{i}" />
					<Type Value="{p['type']}" />
					<Name Value="{p['name']}" />
					<ShortName Value="{p['shortname']}" />
					<MinValue Value="{p['min']}" />
					<MaxValue Value="{p['max']}" />
					<Default Value="{default_val}" />
					<ModType Value="0" />
					<MinMod Value="-1" />
					<MaxMod Value="1" />
					<Timeable>
						<LomId Value="0" />
						<Manual Value="{default_val}" />
						<MidiControllerRange>
							<Min Value="{p['min']}" />
							<Max Value="{p['max']}" />
						</MidiControllerRange>
						<AutomationTarget Id="{i}">
							<LockEnvelope Value="0" />
						</AutomationTarget>
						<ModulationTarget Id="{i}">
							<LockEnvelope Value="0" />
						</ModulationTarget>
					</Timeable>
				</MxDFloatParameter>"""

    # Relative path from User Library root
    rel_path = str(amxd_deploy_path).replace(str(_user_lib_presets().parent) + os.sep, "")
    rel_path = rel_path.replace(str(_user_lib_presets().parent) + "/", "")
    abs_path = str(amxd_deploy_path)
    file_size = amxd_deploy_path.stat().st_size if amxd_deploy_path.exists() else 0

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Ableton MajorVersion="5" MinorVersion="12.0_12120" Creator="m4l_pipeline" Revision="">
	<{device_class}>
		<LomId Value="0" />
		<LomIdView Value="0" />
		<IsExpanded Value="true" />
		<BreakoutIsExpanded Value="false" />
		<On>
			<LomId Value="0" />
			<Manual Value="true" />
			<AutomationTarget Id="100">
				<LockEnvelope Value="0" />
			</AutomationTarget>
			<MidiCCOnOffThresholds>
				<Min Value="64" />
				<Max Value="127" />
			</MidiCCOnOffThresholds>
		</On>
		<ModulationSourceCount Value="0" />
		<ParametersListWrapper LomId="0" />
		<Pointee Id="0" />
		<LastSelectedTimeableIndex Value="0" />
		<LastSelectedClipEnvelopeIndex Value="0" />
		<LastPresetRef>
			<Value />
		</LastPresetRef>
		<LockedScripts />
		<IsFolded Value="false" />
		<ShouldShowPresetName Value="true" />
		<UserName Value="{name}" />
		<Annotation Value="" />
		<SourceContext>
			<Value />
		</SourceContext>
		<MpePitchBendUsesTuning Value="true" />
		<OverwriteProtectionNumber Value="3073" />
		<AudioOutputsListWrapper LomId="0" />
		<AudioInputsListWrapper LomId="0" />
		<MidiOutputsListWrapper LomId="0" />
		<MidiInputsListWrapper LomId="0" />
		<PatchSlot>
			<Value>
				<MxPatchRef Id="1">
					<FileRef>
						<RelativePathType Value="6" />
						<RelativePath Value="{rel_path}" />
						<Path Value="{abs_path}" />
						<Type Value="2" />
						<LivePackName Value="" />
						<LivePackId Value="" />
						<OriginalFileSize Value="{file_size}" />
						<OriginalCrc Value="0" />
					</FileRef>
					<LastModDate Value="0" />
					<SourceContext />
					<SampleUsageHint Value="0" />
				</MxPatchRef>
			</Value>
		</PatchSlot>
		<ParameterList>
			<ParameterList>{param_xml}
			</ParameterList>
		</ParameterList>
		<FileDropList>
			<FileDropList />
		</FileDropList>
		<IdRefList>
			<IdRefList />
		</IdRefList>
		<BlobSlot>
			<Value>
				<MxDBlob Id="99">
					<Blob />
					<HasData Value="false" />
				</MxDBlob>
			</Value>
		</BlobSlot>
		<Routables>
			<InRoutings />
			<OutRoutings />
			<MidiInRoutings />
			<MidiOutRoutings />
		</Routables>
		<MpeEnabled Value="false" />
	</{device_class}>
</Ableton>"""

    if output is None:
        output = WORKSPACE / f"{name}.adv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output, "wb") as f:
        f.write(xml.encode("utf-8"))
    print(f"Built {output} (adv preset, {len(params)} parameters)")
    return output
