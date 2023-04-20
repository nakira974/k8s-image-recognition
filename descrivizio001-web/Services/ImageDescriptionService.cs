using System.Text.Json;
using ImageDescriptorV2.Data;

namespace ImageAnalyzerV1.Services;

public class ImageDescriptionService : IIMageDescriptionService
{
    private ILogger<IIMageDescriptionService> _logger;

    public ImageDescriptionService(ILogger<IIMageDescriptionService> logger)
    {
        _logger = logger;
    }

    public async Task<ImageDescription?> GetImageDescription(string imageUrl)
    {
        ImageDescription? result = null;
        try
        {
            var client = new HttpClient();
            var request = new HttpRequestMessage(HttpMethod.Patch, "http://descrivizio001.lkh.coffee/nakira974/model/descrivizio-001/process");
            request.Headers.Add("Image-Url", imageUrl);
            var response = await client.SendAsync(request);
            response.EnsureSuccessStatusCode();
            result = await JsonSerializer.DeserializeAsync<ImageDescription>(await response.Content.ReadAsStreamAsync());
            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(imageUrl, ": Error while descripting !");
            result = new ImageDescription() {Prediction = ex.Message};
        }

        return result;
    }
}