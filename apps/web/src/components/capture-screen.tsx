'use client';

import {zodResolver} from '@hookform/resolvers/zod';
import {
  Camera,
  CheckCircle2,
  ImagePlus,
  LoaderCircle,
  Lock,
  MapPin,
  Navigation,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react';
import Link from 'next/link';
import {useEffect, useRef, useState} from 'react';
import {useForm} from 'react-hook-form';
import {z} from 'zod';

import {locate, post, uploadPhoto, type UploadAttempt} from '@/lib/api';

const schema = z.object({
  title: z.string().min(3, 'Give your report a short title').max(160),
  category: z.string().min(1),
  description: z.string().max(2000),
  address: z.string().min(2, 'Add a location name'),
  lat: z.coerce.number().min(-90).max(90),
  lng: z.coerce.number().min(-180).max(180),
  severity: z.enum(['low', 'medium', 'high']),
});

type Values = z.output<typeof schema>;
type FormValues = z.input<typeof schema>;
type Props = {cfg: any; notify: (message: string) => void};

const severityHelp = {
  low: ['Low', 'Limited impact; still usable or passable', 15],
  medium: ['Medium', 'Ongoing disruption or safety concern', 25],
  high: ['High', 'Immediate danger or widespread disruption', 50],
} as const;

const preferredCategories = [
  ['garbage_dump', 'Waste'],
  ['pothole', 'Roads / potholes'],
  ['streetlight', 'Streetlights'],
  ['water_leak', 'Water'],
  ['open_drain', 'Drainage'],
  ['other', 'Other'],
] as const;

export function CaptureScreen({cfg, notify}: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [phase, setPhase] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>();
  const attempt = useRef<
    {signature: string; file: File; key: string; finalizeKey: string; id?: string; upload: UploadAttempt}
    | undefined
  >(undefined);
  const form = useForm<FormValues, unknown, Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: '',
      category: 'garbage_dump',
      description: '',
      address: 'Mumbai',
      lat: 19.076,
      lng: 72.8777,
      severity: 'medium',
    },
  });
  const severity = form.watch('severity');

  useEffect(() => {
    const saved = localStorage.getItem('cq_place_draft');
    if (saved) {
      try {
        form.reset({...form.getValues(), ...JSON.parse(saved)});
      } catch {
        localStorage.removeItem('cq_place_draft');
      }
    }
    const subscription = form.watch((value) =>
      localStorage.setItem('cq_place_draft', JSON.stringify(value)),
    );
    return () => subscription.unsubscribe();
  }, [form]);

  useEffect(() => {
    if (!file) {
      setPreview('');
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  async function submit(values: Values) {
    if (!file) {
      setError('Take or choose a photo before submitting.');
      return;
    }
    const payload = {...values, report_type: 'place'};
    const signature = JSON.stringify(payload);
    if (!attempt.current || attempt.current.signature !== signature || attempt.current.file !== file) {
      attempt.current = {
        signature,
        file,
        key: crypto.randomUUID(),
        finalizeKey: crypto.randomUUID(),
        upload: {},
      };
    }
    const current = attempt.current;
    setError('');
    try {
      setPhase('Saving your report…');
      if (!current.id) current.id = (await post('/reports/drafts', payload, current.key)).id;
      setPhase('Securing your photo…');
      await uploadPhoto(`/reports/${current.id}/media/presign`, file, 'evidence', current.upload);
      setPhase('Starting safety checks…');
      setResult(await post(`/reports/${current.id}/finalize`, {}, current.finalizeKey));
      localStorage.removeItem('cq_place_draft');
    } catch (caught: any) {
      setError(`${caught.message} Your draft is saved; retry when you are ready.`);
    } finally {
      setPhase('');
    }
  }

  if (result) {
    return (
      <div className="success-panel">
        <span className="success-icon"><CheckCircle2 size={48}/></span>
        <span className="kicker">REPORT RECEIVED</span>
        <h1>Your civic quest has started.</h1>
        <p>
          Safety checks are running. <strong>{result.provisional_xp} XP is pending</strong> and
          will be released only after verification.
        </p>
        <Link className="button game-cta full" href={`/reports/${result.id}`}>Track this report</Link>
        <Link href="/">Return to Explore</Link>
      </div>
    );
  }

  const allowed = new Map(
    (cfg.categories || [])
      .filter((item: any) => item.report_type === 'place')
      .map((item: any) => [item.code, item.name]),
  );
  const categories = preferredCategories.filter(([code]) => allowed.has(code));
  for (const item of allowed) if (!categories.some(([code]) => code === item[0])) categories.push(item as any);

  return (
    <>
      <header className="page-title">
        <span className="kicker">CAPTURE A PLACE ISSUE</span>
        <h1>What needs attention?</h1>
        <p>A clear photo, accurate location and honest severity help the community verify it.</p>
      </header>
      <div className="capture-kind-card">
        <button className="selected" type="button"><MapPin size={18}/>Place report</button>
        <Link href="/profile/catches/new"><Lock size={16}/>Civic Catch journal</Link>
      </div>
      <form className="capture-mobile" onSubmit={form.handleSubmit(submit)}>
        <section className="form-panel">
          <h2><span className="step-number">1</span>Add live evidence</h2>
          <label className={`upload-area ${preview ? 'has-photo' : ''}`}>
            {preview ? (
              <img src={preview} alt="Your report evidence preview"/>
            ) : (
              <><Camera size={42}/><strong>Take a photo or choose from gallery</strong><span>JPG, PNG, WebP or HEIC · 20 MB maximum</span></>
            )}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
              capture="environment"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
              aria-label="Report photo"
            />
          </label>
          {file && (
            <div className="photo-tools">
              <label className="button outline"><ImagePlus size={15}/>Replace<input type="file" accept="image/*" capture="environment" onChange={(event) => setFile(event.target.files?.[0] || null)}/></label>
              <button type="button" className="button outline" onClick={() => setFile(null)}><X size={15}/>Remove</button>
            </div>
          )}
          <p className="field-note"><ShieldCheck size={15}/>Avoid confrontation and keep identifying details out of the frame.</p>
        </section>

        <section className="form-panel">
          <h2><span className="step-number">2</span>Describe the issue</h2>
          <label>Category<select {...form.register('category')}>{categories.map(([code, name]) => <option key={code} value={code}>{name}</option>)}</select></label>
          <label>Short title<input {...form.register('title')} placeholder="For example: Deep pothole near the bus stop"/></label>
          {form.formState.errors.title && <p className="field-error">{form.formState.errors.title.message}</p>}
          <label>Description <span className="optional">Optional</span><textarea {...form.register('description')} rows={3} placeholder="Add factual context without personal information."/></label>
        </section>

        <section className="form-panel">
          <h2><span className="step-number">3</span>Choose severity</h2>
          <div className="severity-options" role="radiogroup" aria-label="Issue severity">
            {(Object.keys(severityHelp) as Array<keyof typeof severityHelp>).map((value) => {
              const [label, help, xp] = severityHelp[value];
              return <button key={value} type="button" role="radio" aria-checked={severity === value} className={`severity-option ${severity === value ? 'selected' : ''}`} onClick={() => form.setValue('severity', value, {shouldDirty: true})}><strong>{label}</strong><small>{help}</small><b>Pending {xp} XP</b></button>;
            })}
          </div>
          <p className="field-note">A moderator may correct severity with an audit record. Verification releases the accepted reward.</p>
        </section>

        <section className="form-panel">
          <h2><span className="step-number">4</span>Pin the place</h2>
          <button className="button outline full" type="button" onClick={async () => {
            try {
              const position = await locate();
              form.setValue('lat', position.lat);
              form.setValue('lng', position.lng);
              notify('Current location attached.');
            } catch (caught: any) {
              notify(caught.message);
            }
          }}><Navigation size={16}/>Use current location</button>
          <label>Location name<input {...form.register('address')} placeholder="Street, landmark or neighbourhood"/></label>
          <div className="two-fields"><label>Latitude<input type="number" step="any" {...form.register('lat')}/></label><label>Longitude<input type="number" step="any" {...form.register('lng')}/></label></div>
          <p className="field-note">If location permission is unavailable, edit the coordinates manually.</p>
        </section>

        <section className="capture-submit">
          <Sparkles size={24}/>
          <div><strong>{severityHelp[severity][2]} XP pending</strong><small>Released only after accepted verification</small></div>
          <button className="button game-cta full" disabled={Boolean(phase)} type="submit">
            {phase ? <><LoaderCircle className="spin" size={18}/>{phase}</> : <>Submit Place report</>}
          </button>
          {error && <p className="field-error" role="alert">{error}</p>}
          {error && <button type="submit" className="text-button"><RotateCcw size={15}/>Retry saved submission</button>}
        </section>
      </form>
    </>
  );
}
