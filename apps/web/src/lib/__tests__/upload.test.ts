import {afterEach, expect, test, vi} from 'vitest';
import {uploadPhoto, type UploadAttempt} from '../api';

afterEach(()=>vi.unstubAllGlobals());

test('a lost completion response retries the same media without another upload', async()=>{
 vi.stubGlobal('document',{cookie:'cq_csrf=test'});
 const fetcher=vi.fn()
   .mockResolvedValueOnce(Response.json({id:'media-1',upload_url:'/upload',headers:{}}))
   .mockResolvedValueOnce(new Response('',{status:200}))
   .mockRejectedValueOnce(new TypeError('Network interrupted'))
   .mockResolvedValueOnce(Response.json({state:'processed'}));
 vi.stubGlobal('fetch',fetcher);
 const attempt:UploadAttempt={};const file=new File(['synthetic'],'photo.jpg',{type:'image/jpeg'});
 await expect(uploadPhoto('/reports/one/media/presign',file,'evidence',attempt)).rejects.toThrow('Network interrupted');
 await expect(uploadPhoto('/reports/one/media/presign',file,'evidence',attempt)).resolves.toBe('media-1');
 expect(fetcher.mock.calls.map(call=>call[0])).toEqual([
  '/api/v1/reports/one/media/presign','/upload','/api/v1/media/media-1/complete','/api/v1/media/media-1/complete']);
 await uploadPhoto('/reports/one/media/presign',file,'evidence',attempt);
 expect(fetcher).toHaveBeenCalledTimes(4);
});
