package com.example.kabaaragent.data

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

interface DataRepository {
    val currentResponse: Flow<PipelineResponse?>
    suspend fun processScrap(description: String, imageBase64: String? = null): PipelineResponse
}

class DefaultDataRepository : DataRepository {
    private val _currentResponse = MutableStateFlow<PipelineResponse?>(null)
    override val currentResponse = _currentResponse.asStateFlow()

    override suspend fun processScrap(description: String, imageBase64: String?): PipelineResponse {
        val request = AppraisalRequest(description = description, image_base64 = imageBase64)
        val response = KabaarApiClient.apiService.runPipeline(request)
        _currentResponse.value = response
        return response
    }
}
